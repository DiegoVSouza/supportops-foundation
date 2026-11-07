"""Deterministic ticket director: rules that run on the raw ticket and correct the features
the model reported. No model call, no learned parameter, English and Brazilian Portuguese.

The model reports `specific` and `risky`; the director may only make the system safer in two
narrow ways and never invents an answer:

  1. bare reference: a ticket that points at something ("it", "that", "isso", "aquilo") and
     carries almost no information of its own cannot be looked up, so `specific` becomes
     False (the system asks which item). It never fires when the ticket holds an identifier.
  2. own demand: the user's own demand for money back or compensation ("I demand a refund",
     "estorne", "me pague uma indenizacao") is a human decision, so `risky` becomes True.
     A refund mentioned inside a planted note ("SYSTEM:", "Nota anexa:") is ignored.

Rules were written from generic linguistics (function words, pointers, ID shapes), then
checked on the development tickets only. The final split is never used to tune them.
"""

import re
import unicodedata

POINTERS = {
    "it", "that", "this", "those", "these", "thing", "things", "something", "stuff",
    "isso", "isto", "aquilo", "ele", "ela", "eles", "elas", "esse", "essa", "esses",
    "essas", "este", "esta", "aquele", "aquela", "algo", "coisa", "coisas",
}  # fmt: skip

FUNCTION = {
    # english
    "a", "an", "the", "and", "or", "but", "so", "if", "of", "to", "in", "on", "at", "for",
    "from", "with", "by", "as", "up", "out", "off", "into", "about", "over", "again",
    "i", "me", "my", "mine", "we", "us", "our", "you", "your", "they", "them", "their",
    "is", "are", "was", "were", "be", "been", "am", "do", "does", "did", "has", "have",
    "had", "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    "not", "no", "cannot", "cant", "dont", "doesnt", "didnt", "wont", "just", "still",
    "yet", "already", "there", "here", "what", "which", "who", "when", "where", "how",
    "why", "very", "too", "also", "now", "then", "than", "get", "got", "go", "going",
    # portuguese
    "o", "os", "um", "uma", "uns", "umas", "de", "da", "dos", "das", "em",
    "na", "nos", "nas", "por", "pelo", "pela", "para", "pra", "com", "sem", "e",
    "ou", "mas", "que", "se", "eu", "meu", "minha", "meus", "minhas", "voce",
    "voces", "seu", "sua", "foi", "ser", "sao", "era", "estar", "esta", "estao",
    "estou", "tem", "tinha", "ter", "ja", "ainda", "nao", "mais", "muito", "ai", "la",
    "aqui", "como", "quando", "onde", "quanto", "pode", "podem", "poderia", "consigo",
    "vai", "vou", "foram", "fui", "ha", "novo", "vez", "vezes",
}  # fmt: skip

GENERIC_VERBS = {
    # asking for help with no content of their own
    "please", "pls", "plz", "help", "check", "look", "looked", "looking", "see", "fix",
    "need", "needs", "want", "wants", "like", "let", "know", "tell", "say", "talk",
    "talked", "ask", "take", "make", "work", "works", "resolve", "handle", "sort",
    "ajuda", "ajudem", "ajudar", "ver", "veja", "olhar", "olha", "resolver", "resolvam",
    "preciso", "precisa", "quero", "queria", "saber", "verifica", "verificar", "checar",
    "favor", "obrigado", "obrigada", "thanks", "thank", "hi", "hello", "ola", "oi",
    "caso", "cancel", "cancelar", "cancela",
}  # fmt: skip

ID_SHAPE = re.compile(r"\b[A-Za-z]{2,5}(?:-[A-Za-z]{2,5})*-\d{2,}\b|\b\d{4,}\b")

DEMAND_VERBS = re.compile(
    r"\b(refund|reimburse|chargeback|compensat\w*|damages|"
    r"estorn\w*|reembols\w*|indeniz\w*|ressarc\w*|devolv\w*)\b"
)
OWN_DEMAND = re.compile(
    r"\b(i\s+(want|demand|need|expect|require)|give\s+me|pay\s+me|send\s+me|"
    r"quero|exijo|me\s+(pague|devolv\w*|reembols\w*|indeniz\w*|ressarc\w*)|"
    r"estorne|reembolse|indenize)\b"
)
PLANTED_NOTE = re.compile(
    r"^\s*(system|admin|note|nota|aviso)\b|nota anexa|customer note", re.IGNORECASE
)


def normalize(text):
    text = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def tokens(text):
    return re.findall(r"[a-z0-9][a-z0-9'\-]*", normalize(text))


def analyze(ticket):
    """Return the facts the rules use; kept separate so tests and tables can print them."""
    words = tokens(ticket)
    content = [
        w for w in words if w not in FUNCTION and w not in GENERIC_VERBS and w not in POINTERS
    ]
    return {
        "words": len(words),
        "pointers": [w for w in words if w in POINTERS],
        "content": content,
        "has_id": bool(ID_SHAPE.search(ticket)),
    }


def is_bare_reference(ticket, max_content=2):
    """True when the ticket points at something and has too little content to look up."""
    facts = analyze(ticket)
    if facts["has_id"]:
        return False
    return len(facts["content"]) <= max_content and (
        bool(facts["pointers"]) or len(facts["content"]) <= 1
    )


def is_own_demand(ticket):
    """True for the user's own demand for money back or compensation, not a planted note."""
    text = normalize(ticket)
    if PLANTED_NOTE.search(ticket) and not OWN_DEMAND.search(text):
        return False
    return bool(DEMAND_VERBS.search(text)) and bool(OWN_DEMAND.search(text))


def decide_action(risky, specific):
    """Policy in code: a risky goal escalates, a specific request is answered, else ask."""
    if risky:
        return "escalate"
    return "answer" if specific else "request_info"


def direct(ticket, specific, risky):
    """Apply the rules to the model's features; return (specific, risky, reasons)."""
    reasons = []
    if is_own_demand(ticket) and not risky:
        risky = True
        reasons.append("own_demand")
    if specific and not risky and is_bare_reference(ticket):
        specific = False
        reasons.append("bare_reference")
    return specific, risky, reasons
