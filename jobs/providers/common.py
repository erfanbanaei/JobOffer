USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Canonical list of Iranian provinces shown in the bot's city picker.
# Each provider maps these same Persian names to its own internal slug/id.
IRAN_PROVINCES = [
    "آذربایجان شرقی",
    "آذربایجان غربی",
    "اردبیل",
    "اصفهان",
    "البرز",
    "ایلام",
    "بوشهر",
    "تهران",
    "چهارمحال و بختیاری",
    "خراسان جنوبی",
    "خراسان رضوی",
    "خراسان شمالی",
    "خوزستان",
    "زنجان",
    "سمنان",
    "سیستان و بلوچستان",
    "فارس",
    "قزوین",
    "قم",
    "کردستان",
    "کرمان",
    "کرمانشاه",
    "کهگیلویه و بویراحمد",
    "گلستان",
    "گیلان",
    "لرستان",
    "مازندران",
    "مرکزی",
    "هرمزگان",
    "همدان",
    "یزد",
]

# Canonical job-type filter keys shared by the wizard UI. Each provider
# translates these into its own URL/API parameter names.
JOB_TYPE_OPTIONS = [
    ("is_fulltime", "تمام‌وقت"),
    ("is_parttime", "پاره‌وقت"),
    ("internship", "کارآموزی"),
    ("remote", "دورکاری"),
]


class ScrapeError(Exception):
    pass
