# BiblioTech v1.3
# gestion de la bibliotheque municipale
# auteur : stagiaire 2019, modifie par plusieurs personnes depuis

import contextlib
import os
import sys
from datetime import date, datetime, timedelta

DATA = os.environ.get("BIBLIOTECH_DATA", "data")
TODAY = None
debug = False

# --- Constantes métier ---
BOOK_LOAN_DAYS = 21
DVD_LOAN_DAYS = 7
MAGAZINE_LOAN_DAYS = 3

LOAN_DURATIONS = {
    "book": BOOK_LOAN_DAYS,
    "dvd": DVD_LOAN_DAYS,
    "magazine": MAGAZINE_LOAN_DAYS,
}

MAX_LOANS_STUDENT = 5
MAX_LOANS_PREMIUM = 8
MAX_LOANS_STANDARD = 3

MAX_LOANS_BY_MEMBER_TYPE = {
    "student": MAX_LOANS_STUDENT,
    "premium": MAX_LOANS_PREMIUM,
    "standard": MAX_LOANS_STANDARD,
}

DAILY_FEE_BOOK = 0.50
DAILY_FEE_DVD = 1.00
DAILY_FEE_MAGAZINE = 0.20

DAILY_FEES = {
    "book": DAILY_FEE_BOOK,
    "dvd": DAILY_FEE_DVD,
    "magazine": DAILY_FEE_MAGAZINE,
}


def late_fee(days_late: int, kind: str, member_type: str, book_price: float) -> float:
    """Calcule la penalite de retard."""
    if days_late <= 0:
        return 0.0
    daily_fee = DAILY_FEES.get(kind, DAILY_FEE_BOOK)
    fee = days_late * daily_fee
    if member_type == "student":
        fee *= 0.5
    elif member_type == "premium":
        fee = 0.0
    if fee > book_price:
        fee = book_price
    return round(fee, 2)


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
            active = x[4] == "1"
            self.m.append(
                {
                    "id": x[0],
                    "name": x[1],
                    "email": x[2],
                    "type": x[3],
                    "active": active,
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

    # chargement des donnees
    def load(self):
        self._load_books()
        self._load_members()
        self._load_loans()
        if debug:
            print("chargement ok", len(self.b), len(self.m), len(self.l))

    def save(self):
        with open(DATA + "/loans.csv", "w", encoding="utf-8") as f:
            f.write("id;member_id;book_id;start;due;returned;fee\n")
            for x in self.l:
                f.write(
                    f"{x['id']};{x['member']};{x['book']};{x['start']};{x['due']};"
                    f"{x['returned']};{x['fee']:.2f}\n"
                )

    # t = "b" pour livre, "m" pour membre, "l" pour emprunt
    def find(self, t, id):
        collection = {"b": self.b, "m": self.m, "l": self.l}.get(t, [])
        for x in collection:
            if x["id"] == id:
                return x
        return None

    def nb(self, mid):
        return sum(1 for x in self.l if x["member"] == mid and x["returned"] == "")

    def dispo(self, bid):
        bk = self.find("b", bid)
        n = sum(1 for x in self.l if x["book"] == bid and x["returned"] == "")
        return bk["copies"] - n

    def _has_overdue_loans(self, mid):
        today = get_today()
        for x in self.l:
            if (
                x["member"] == mid
                and x["returned"] == ""
                and date.fromisoformat(x["due"]) < today
            ):
                return True
        return False

    def _is_already_borrowed(self, mid, bid):
        for x in self.l:
            if x["member"] == mid and x["book"] == bid and x["returned"] == "":
                return True
        return False

    def _next_loan_id(self):
        max_id = max([int(x["id"][1:]) for x in self.l], default=0)
        return "L" + str(max_id + 1).zfill(3)

    # emprunter un document
    def do_stuff(self, mid, bid):
        mb = self.find("m", mid)
        if mb is None:
            print("Erreur : membre inconnu")
            return False

        bk = self.find("b", bid)
        if bk is None:
            print("Erreur : livre inconnu")
            return False

        if not mb["active"]:
            print("Refus : membre inactif")
            return False

        if self._has_overdue_loans(mid):
            print("Refus : emprunts en retard")
            return False

        max_allowed = MAX_LOANS_BY_MEMBER_TYPE.get(mb["type"], MAX_LOANS_STANDARD)
        if self.nb(mid) >= max_allowed:
            print(f"Refus : limite d'emprunts atteinte ({max_allowed})")
            return False

        if self._is_already_borrowed(mid, bid):
            print("Refus : deja emprunte par ce membre")
            return False

        if self.dispo(bid) <= 0:
            print("Refus : plus d'exemplaire disponible")
            return False

        days = LOAN_DURATIONS.get(bk["kind"], BOOK_LOAN_DAYS)
        today = get_today()
        due = today + timedelta(days=days)
        new_id = self._next_loan_id()
        self.l.append(
            {
                "id": new_id,
                "member": mid,
                "book": bid,
                "start": str(today),
                "due": str(due),
                "returned": "",
                "fee": 0,
            }
        )
        self.save()
        print(
            f"Emprunt {new_id} enregistre : {bk['title']} pour {mb['name']}, "
            f"retour avant le {due}"
        )
        return True

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
        due_date = date.fromisoformat(ln["due"])
        days_late = max(0, (t - due_date).days)
        fee = late_fee(days_late, bk["kind"], mb["type"], bk["price"])

        ln["returned"] = str(t)
        ln["fee"] = fee
        self.save()
        print(
            f"Retour enregistre : {bk['title']}. Retard : {days_late} jour(s). "
            f"Penalite : {fee:.2f} EUR"
        )

    # liste des retards + envoi des rappels
    def overdue(self):
        today = get_today()
        overdue_list = [
            x
            for x in self.l
            if x["returned"] == "" and date.fromisoformat(x["due"]) < today
        ]
        if not overdue_list:
            print("Aucun retard.")
            return

        overdue_list.sort(key=lambda x: (x["due"], x["id"]))
        total = 0.0
        for x in overdue_list:
            book = self.find("b", x["book"])
            member = self.find("m", x["member"])
            nbj = (today - date.fromisoformat(x["due"])).days
            p = late_fee(nbj, book["kind"], member["type"], book["price"])
            total += p
            print(
                f"{x['id']} | {member['name']} | {book['title']} | "
                f"{nbj} jour(s) | {p:.2f} EUR"
            )
            print(
                f"EMAIL -> {member['email']} : Rappel, vous devez rendre "
                f"'{book['title']}' (retard {nbj} jours)"
            )
        print(f"Total des penalites en cours : {total:.2f} EUR")

    def _report_titles_and_members(self):
        total_copies = sum(x["copies"] for x in self.b)
        print(f"Titres : {len(self.b)} ({total_copies} exemplaires)")
        active_count = sum(1 for x in self.m if x["active"])
        print(f"Membres : {len(self.m)} dont {active_count} actifs")

    def _report_stats(self):
        today = get_today()
        en_cours = 0
        en_retard = 0
        encaisse = 0.0
        a_payer = 0.0
        counts_by_book = {}
        counts_by_kind = {}

        for x in self.l:
            bk = self.find("b", x["book"])
            counts_by_kind[bk["kind"]] = counts_by_kind.get(bk["kind"], 0) + 1
            counts_by_book[x["book"]] = counts_by_book.get(x["book"], 0) + 1

            if x["returned"] == "":
                en_cours += 1
                due_date = date.fromisoformat(x["due"])
                if due_date < today:
                    en_retard += 1
                    mb = self.find("m", x["member"])
                    days_late = (today - due_date).days
                    a_payer += late_fee(days_late, bk["kind"], mb["type"], bk["price"])
            else:
                encaisse += x["fee"]

        print(
            f"Emprunts : {len(self.l)} au total, {en_cours} en cours, "
            f"{en_retard} en retard"
        )
        print(f"Penalites encaissees : {encaisse:.2f} EUR")
        print(f"Penalites en attente : {a_payer:.2f} EUR")

        for k in sorted(counts_by_kind.keys()):
            print(f"  - {k} : {counts_by_kind[k]} emprunt(s)")

        self._report_top3(counts_by_book)

    def _report_top3(self, counts_by_book):
        ranked = sorted(
            [(-c, self.find("b", bid)["title"]) for bid, c in counts_by_book.items()]
        )
        print("Top 3 :")
        for i, (neg_count, title) in enumerate(ranked[:3]):
            count = -neg_count
            print(f"  {i + 1}. {title} ({count})")

    def report(self):
        print("=== RAPPORT BIBLIOTECH ===")
        print(f"Date : {get_today()}")
        self._report_titles_and_members()
        self._report_stats()

    def export(self, fname, sep=";"):
        today = get_today()
        with open(fname, "w", encoding="utf-8") as f:
            f.write(
                f"loan_id{sep}member{sep}title{sep}start{sep}due{sep}"
                f"returned{sep}days_late{sep}fee\n"
            )
            for x in self.l:
                bk = self.find("b", x["book"])
                mb = self.find("m", x["member"])
                end = date.fromisoformat(x["returned"]) if x["returned"] else today
                due = date.fromisoformat(x["due"])
                days_late = max(0, (end - due).days)
                fee = late_fee(days_late, bk["kind"], mb["type"], bk["price"])
                f.write(
                    f"{x['id']}{sep}{mb['name']}{sep}{bk['title']}{sep}{x['start']}"
                    f"{sep}{x['due']}{sep}{x['returned']}{sep}{days_late}{sep}"
                    f"{fee:.2f}\n"
                )
        print(f"Export termine : {len(self.l)} lignes dans {fname}")

    # systeme de plugins (pour plus tard)
    def register_plugin(self, name, fn, priority=0, options=None):
        if options is None:
            options = {}
        self.plugins[name] = {"fn": fn, "priority": priority, "options": options}

    def run_plugins(self, event, payload=None):
        res = []
        for name in sorted(self.plugins, key=lambda n: self.plugins[n]["priority"]):
            with contextlib.suppress(Exception):
                res.append(
                    self.plugins[name]["fn"](
                        event, payload, **self.plugins[name]["options"]
                    )
                )
        return res


def get_today():
    global TODAY
    if TODAY is None:
        return date.today()
    return TODAY


def handle_list(lib, args):
    for x in lib.b:
        n = lib.dispo(x["id"])
        print(
            f"{x['id']} | {x['title']} | {x['author']} | {x['kind']} | "
            f"{n}/{x['copies']} disponible(s)"
        )
    return 0


def handle_members(lib, args):
    for x in lib.m:
        s = "actif" if x["active"] else "inactif"
        print(
            f"{x['id']} | {x['name']} | {x['type']} | {s} | "
            f"{lib.nb(x['id'])} emprunt(s) en cours"
        )
    return 0


def handle_borrow(lib, args):
    if len(args) < 3:
        print("Usage : borrow <id_membre> <id_document>")
        return 1
    r = lib.do_stuff(args[1], args[2])
    return 0 if r else 2


def handle_return(lib, args):
    if len(args) < 2:
        print("Usage : return <id_emprunt>")
        return 1
    lib.ret(args[1])
    return 0


def handle_overdue(lib, args):
    lib.overdue()
    return 0


def handle_report(lib, args):
    lib.report()
    return 0


def handle_export(lib, args):
    if len(args) < 2:
        print("Usage : export <fichier.csv>")
        return 1
    lib.export(args[1], ";")
    return 0


COMMANDS = {
    "list": handle_list,
    "members": handle_members,
    "borrow": handle_borrow,
    "return": handle_return,
    "overdue": handle_overdue,
    "report": handle_report,
    "export": handle_export,
}


def process(args):
    lib = Library()
    if not args:
        print(
            "Usage : python bibliotech.py <commande> [arguments] [--today AAAA-MM-JJ]"
        )
        print("Commandes : list, members, borrow, return, overdue, report, export")
        return 1
    cmd = args[0]
    handler = COMMANDS.get(cmd)
    if handler is None:
        print("Commande inconnue : " + cmd)
        return 1
    return handler(lib, args)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--today" in a:
        i = a.index("--today")
        TODAY = datetime.strptime(a[i + 1], "%Y-%m-%d").date()
        a = a[:i] + a[i + 2 :]
    if "--debug" in a:
        debug = True
        a.remove("--debug")
    sys.exit(process(a))
