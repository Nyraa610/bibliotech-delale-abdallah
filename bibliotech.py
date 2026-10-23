# BiblioTech v1.3
# gestion de la bibliotheque municipale
# auteur : stagiaire 2019, modifie par plusieurs personnes depuis

import logging
import os
import sys
from datetime import date, datetime, timedelta

DATA = os.environ.get("BIBLIOTECH_DATA", "data")
TODAY = None
debug = False

# --- Règles de calcul et pénalités ---
DAILY_FEE_BY_KIND = {"book": 0.5, "dvd": 1.0, "magazine": 0.2}
DEFAULT_DAILY_FEE = 0.5
DISCOUNT_BY_MEMBER_TYPE = {"student": 0.5, "premium": 1.0}

LOAN_DURATION_BY_KIND = {"book": 21, "dvd": 7, "magazine": 3}
DEFAULT_LOAN_DURATION = 21

MAX_LOANS_BY_MEMBER_TYPE = {"student": 5, "premium": 8, "standard": 3}
DEFAULT_MAX_LOANS = 3


def late_fee(days_late: int, kind: str, member_type: str, price: float) -> float:
    """Pénalité de retard, réduite selon le membre et plafonnée au prix."""
    if days_late <= 0:
        return 0.0

    fee = days_late * DAILY_FEE_BY_KIND.get(kind, DEFAULT_DAILY_FEE)
    fee *= 1 - DISCOUNT_BY_MEMBER_TYPE.get(member_type, 0.0)
    return round(min(fee, price), 2)


def parse_date(text: str) -> date:
    """Convertit une chaîne AAAA-MM-JJ en objet date."""
    return datetime.strptime(text, "%Y-%m-%d").date()


class Library:
    def __init__(self):
        self.b = []
        self.m = []
        self.l = []
        self.plugins = {}
        self.load()

    def _load_books(self):
        with open(DATA + "/books.csv", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[1:]:
            if not line.strip():
                continue
            x = line.strip().split(";")
            self.b.append(
                {
                    "id": x[0],
                    "title": x[1],
                    "author": x[2],
                    "kind": x[3],
                    "price": float(x[4]),
                    "copies": int(x[5]),
                }
            )

    def _load_members(self):
        with open(DATA + "/members.csv", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[1:]:
            if not line.strip():
                continue
            x = line.strip().split(";")
            self.m.append(
                {
                    "id": x[0],
                    "name": x[1],
                    "email": x[2],
                    "type": x[3],
                    "active": x[4] == "1",
                }
            )

    def _load_loans(self):
        with open(DATA + "/loans.csv", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[1:]:
            if not line.strip():
                continue
            x = line.strip().split(";")
            try:
                fee = float(x[6])
            except (ValueError, IndexError):
                fee = 0.0
            self.l.append(
                {
                    "id": x[0],
                    "member": x[1],
                    "book": x[2],
                    "start": x[3],
                    "due": x[4],
                    "returned": x[5],
                    "fee": fee,
                }
            )

    def load(self):
        self._load_books()
        self._load_members()
        self._load_loans()
        if debug:
            print("chargement ok", len(self.b), len(self.m), len(self.l))

    def save(self):
        with open(DATA + "/loans.csv", "w", encoding="utf-8") as f:
            f.write("id;member_id;book_id;start;due;returned;fee\n")
            for loan in self.l:
                f.write(
                    f"{loan['id']};{loan['member']};{loan['book']};{loan['start']};"
                    f"{loan['due']};{loan['returned']};{loan['fee']:.2f}\n"
                )

    # t = "b" pour livre, "m" pour membre, "l" pour emprunt
    def find(self, t, id):
        if t == "b":
            for x in self.b:
                if x["id"] == id:
                    return x
        elif t == "m":
            for x in self.m:
                if x["id"] == id:
                    return x
        elif t == "l":
            for x in self.l:
                if x["id"] == id:
                    return x
        return None

    def nb(self, mid):
        n = 0
        for x in self.l:
            if x["member"] == mid and x["returned"] == "":
                n = n + 1
        return n

    def dispo(self, bid):
        bk = self.find("b", bid)
        n = 0
        for x in self.l:
            if x["book"] == bid and x["returned"] == "":
                n = n + 1
        return bk["copies"] - n

    def has_overdue_loan(self, member_id):
        today = get_today()
        for x in self.l:
            if x["member"] == member_id and x["returned"] == "":
                if parse_date(x["due"]) < today:
                    return True
        return False

    def is_borrowing(self, member_id, book_id):
        for x in self.l:
            if (
                x["member"] == member_id
                and x["book"] == book_id
                and x["returned"] == ""
            ):
                return True
        return False

    def refusal_reason(self, member, book):
        if not member["active"]:
            return "Refus : membre inactif"
        if self.has_overdue_loan(member["id"]):
            return "Refus : emprunts en retard"
        limit = MAX_LOANS_BY_MEMBER_TYPE.get(member["type"], DEFAULT_MAX_LOANS)
        if self.nb(member["id"]) >= limit:
            return f"Refus : limite d'emprunts atteinte ({limit})"
        if self.is_borrowing(member["id"], book["id"]):
            return "Refus : deja emprunte par ce membre"
        if self.dispo(book["id"]) <= 0:
            return "Refus : plus d'exemplaire disponible"
        return None

    def create_loan(self, member, book):
        days = LOAN_DURATION_BY_KIND.get(book["kind"], DEFAULT_LOAN_DURATION)
        today = get_today()
        due = today + timedelta(days=days)
        max_id = max([int(x["id"][1:]) for x in self.l], default=0)
        new_id = "L" + str(max_id + 1).zfill(3)
        self.l.append(
            {
                "id": new_id,
                "member": member["id"],
                "book": book["id"],
                "start": str(today),
                "due": str(due),
                "returned": "",
                "fee": 0,
            }
        )
        self.save()
        print(
            f"Emprunt {new_id} enregistre : {book['title']} pour {member['name']}, retour avant le {due}"
        )
        return True

    def borrow(self, member_id, book_id):
        member = self.find("m", member_id)
        if member is None:
            print("Erreur : membre inconnu")
            return False
        book = self.find("b", book_id)
        if book is None:
            print("Erreur : livre inconnu")
            return False

        reason = self.refusal_reason(member, book)
        if reason is not None:
            print(reason)
            return False

        return self.create_loan(member, book)

    # Compatibilité avec l'ancien nom de méthode
    do_stuff = borrow

    # retour d'un document
    def ret(self, lid):
        ln = self.find("l", lid)
        if ln is None:
            print("Erreur : emprunt inconnu")
            return
        if ln["returned"] != "":
            print("Erreur : emprunt deja rendu")
            return
        bk = self.find("b", ln["book"])
        mb = self.find("m", ln["member"])
        t = get_today()
        due_date = parse_date(ln["due"])
        days_late = max(0, (t - due_date).days)
        fee = late_fee(days_late, bk["kind"], mb["type"], bk["price"])

        ln["returned"] = str(t)
        ln["fee"] = fee
        self.save()
        print(
            "Retour enregistre : "
            + bk["title"]
            + ". Retard : "
            + str(days_late)
            + " jour(s). Penalite : "
            + "%.2f" % fee
            + " EUR"
        )

    # liste des retards + envoi des rappels
    def overdue(self):
        tmp = []
        for x in self.l:
            if x["returned"] == "":
                if parse_date(x["due"]) < get_today():
                    tmp.append(x)
        if len(tmp) == 0:
            print("Aucun retard.")
            return
        tmp.sort(key=lambda x: (x["due"], x["id"]))
        total = 0
        for x in tmp:
            book = self.find("b", x["book"])
            member = self.find("m", x["member"])
            nbj = (get_today() - parse_date(x["due"])).days
            p = late_fee(nbj, book["kind"], member["type"], book["price"])
            total = total + p
            print(
                x["id"]
                + " | "
                + member["name"]
                + " | "
                + book["title"]
                + " | "
                + str(nbj)
                + " jour(s) | "
                + "%.2f" % p
                + " EUR"
            )
            print(
                "EMAIL -> "
                + member["email"]
                + " : Rappel, vous devez rendre '"
                + book["title"]
                + "' (retard "
                + str(nbj)
                + " jours)"
            )
        print("Total des penalites en cours : " + "%.2f" % total + " EUR")

    def report(self):
        data2 = {}
        print("=== RAPPORT BIBLIOTECH ===")
        print("Date : " + str(get_today()))
        c = 0
        for x in self.b:
            c = c + x["copies"]
        print("Titres : " + str(len(self.b)) + " (" + str(c) + " exemplaires)")
        a = 0
        for x in self.m:
            if x["active"]:
                a = a + 1
        print("Membres : " + str(len(self.m)) + " dont " + str(a) + " actifs")
        en_cours = 0
        en_retard = 0
        encaisse = 0
        a_payer = 0
        for x in self.l:
            if x["returned"] == "":
                en_cours = en_cours + 1
                due = parse_date(x["due"])
                if due < get_today():
                    en_retard = en_retard + 1
                    bk = self.find("b", x["book"])
                    mb = self.find("m", x["member"])
                    j = (get_today() - due).days
                    pen = late_fee(j, bk["kind"], mb["type"], bk["price"])
                    a_payer = a_payer + pen
            else:
                encaisse = encaisse + x["fee"]
            if x["book"] in data2:
                data2[x["book"]] = data2[x["book"]] + 1
            else:
                data2[x["book"]] = 1
        print(
            "Emprunts : "
            + str(len(self.l))
            + " au total, "
            + str(en_cours)
            + " en cours, "
            + str(en_retard)
            + " en retard"
        )
        print("Penalites encaissees : " + "%.2f" % encaisse + " EUR")
        print("Penalites en attente : " + "%.2f" % a_payer + " EUR")
        k = {}
        for x in self.l:
            bk = self.find("b", x["book"])
            if bk["kind"] in k:
                k[bk["kind"]] += 1
            else:
                k[bk["kind"]] = 1
        for kk in sorted(k.keys()):
            print("  - " + kk + " : " + str(k[kk]) + " emprunt(s)")
        lst = []
        for key in data2:
            lst.append((-data2[key], self.find("b", key)["title"]))
        lst.sort()
        print("Top 3 :")
        i = 0
        for x in lst:
            if i < 3:
                print("  " + str(i + 1) + ". " + x[1] + " (" + str(-x[0]) + ")")
            i = i + 1

    def export(self, fname, sep):
        n = 0
        with open(fname, "w", encoding="utf-8") as f:
            f.write(
                "loan_id"
                + sep
                + "member"
                + sep
                + "title"
                + sep
                + "start"
                + sep
                + "due"
                + sep
                + "returned"
                + sep
                + "days_late"
                + sep
                + "fee\n"
            )
            for x in self.l:
                bk = self.find("b", x["book"])
                mb = self.find("m", x["member"])
                if x["returned"] != "":
                    end = parse_date(x["returned"])
                else:
                    end = get_today()
                dl = max(0, (end - parse_date(x["due"])).days)
                fee = late_fee(dl, bk["kind"], mb["type"], bk["price"])
                f.write(
                    x["id"]
                    + sep
                    + mb["name"]
                    + sep
                    + bk["title"]
                    + sep
                    + x["start"]
                    + sep
                    + x["due"]
                    + sep
                    + x["returned"]
                    + sep
                    + str(dl)
                    + sep
                    + "%.2f" % fee
                    + "\n"
                )
                n = n + 1
        print("Export termine : " + str(n) + " lignes dans " + fname)


    # systeme de plugins (pour plus tard)
    def register_plugin(self, name, fn, priority=0, options=None):
        if options is None:
            options = {}
        self.plugins[name] = {"fn": fn, "priority": priority, "options": options}

    def run_plugins(self, event, payload=None):
        res = []
        for name in sorted(self.plugins, key=lambda n: self.plugins[n]["priority"]):
            try:
                res.append(
                    self.plugins[name]["fn"](
                        event, payload, **self.plugins[name]["options"]
                    )
                )
            except Exception:
                logging.exception("Erreur dans le plugin %s", name)
        return res


def get_today():
    global TODAY
    if TODAY is None:
        return date.today()
    return TODAY


def process(args):
    global TODAY
    lib = Library()
    if len(args) == 0:
        print(
            "Usage : python bibliotech.py <commande> [arguments] [--today AAAA-MM-JJ]"
        )
        print("Commandes : list, members, borrow, return, overdue, report, export")
        return 1
    cmd = args[0]
    if cmd == "list":
        for x in lib.b:
            n = lib.dispo(x["id"])
            print(
                x["id"]
                + " | "
                + x["title"]
                + " | "
                + x["author"]
                + " | "
                + x["kind"]
                + " | "
                + str(n)
                + "/"
                + str(x["copies"])
                + " disponible(s)"
            )
    elif cmd == "members":
        for x in lib.m:
            if x["active"]:
                s = "actif"
            else:
                s = "inactif"
            print(
                x["id"]
                + " | "
                + x["name"]
                + " | "
                + x["type"]
                + " | "
                + s
                + " | "
                + str(lib.nb(x["id"]))
                + " emprunt(s) en cours"
            )
    elif cmd == "borrow":
        if len(args) < 3:
            print("Usage : borrow <id_membre> <id_document>")
            return 1
        r = lib.borrow(args[1], args[2])
        if r is False:
            return 2
    elif cmd == "return":
        if len(args) < 2:
            print("Usage : return <id_emprunt>")
            return 1
        lib.ret(args[1])
    elif cmd == "overdue":
        lib.overdue()
    elif cmd == "report":
        lib.report()
    elif cmd == "export":
        if len(args) < 2:
            print("Usage : export <fichier.csv>")
            return 1
        lib.export(args[1], ";")
    else:
        print("Commande inconnue : " + cmd)
        return 1
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--today" in a:
        i = a.index("--today")
        TODAY = parse_date(a[i + 1])
        a = a[:i] + a[i + 2 :]
    if "--debug" in a:
        debug = True
        a.remove("--debug")
    sys.exit(process(a))