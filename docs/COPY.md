# User-facing Hebrew copy

Every Hebrew string a user can see, as of 2026-10-28. Status:
**decided** = fixed by SPEC (change it there first, with a DECISIONS
entry); **placeholder** = written for the build, for the owner to
replace; **placeholder → owner-approved** = the owner's text (2026-10-28). `{x}` marks a value filled in at run time.

Some texts exist in more than one place (marked **same as**). They must
be changed together.

Not listed (not copy): the letter tables in `web/js/letters.js` and
`api/src/borer_api/words.py`, the warm-up text in
`api/src/borer_api/app.py` (never shown), and code comments.

## Page frame — `web/index.html`

| Key | Where it appears | Current text | Status |
|---|---|---|---|
| `<title>` | browser tab (replaced by the preview tags, see `og.py`) | הבורר | decided (name) |
| header brand | top of every page | הבורר | decided (name) |
| header subtitle | under the brand, every page | בית המשפט העליון לענייני זבובים | placeholder; same as `ogimage.py` header |
| footer | bottom of every page | 140 אלף נוירונים של מוח זבוב אמיתי. בלי AI. · איך זה עובד? | placeholder; same as `LAB.noAi`, `ogimage.FOOTER` |

## Page copy — `web/js/copy.js` (`T`)

| Key | Where it appears | Current text | Status |
|---|---|---|---|
| `T.title` | not shown (kept for the pages) | הבורר | decided (name) |
| `T.tagline` | open-case screen, above the form | יש ויכוח? תנו לזבוב להכריע. | placeholder → owner-approved |
| `T.topic` | open-case form, topic label | על מה הוויכוח? (לא חובה) | placeholder |
| `T.topicHint` | open-case form, under the topic | הזבוב לא טועם את הנושא, הוא רק יופיע בפסק הדין | placeholder |
| `T.yourName` | open-case form, A's name label | השם שלך | placeholder |
| `T.otherName` | open-case form, B's name label | השם של הצד השני | placeholder |
| `T.yourArgument` | argument label (A's and B's forms); A's waiting page | הטענה שלך | placeholder |
| `T.argumentPlaceholder` | inside the argument box | למה אני צודק/ת… | placeholder |
| `T.blindHint` | open-case form, under A's argument | הצד השני לא יראה את הטענה שלך לפני שיגיש את שלו | placeholder |
| `T.blindHintB` | B's form | את הטענה של {name A} תראו רק אחרי שתגישו את שלכם | placeholder |
| `T.open` | open-case button | לפתוח תיק | placeholder |
| `T.opening` | open-case button while sending | פותחים את התיק… | placeholder |
| `T.letters` | argument counter | {n}/{min} אותיות בעברית | placeholder |
| `T.chars` | argument counter | {n}/{max} תווים | placeholder |
| `T.noConnection` | any screen, network error | אין חיבור לשרת. נסו שוב | placeholder |
| `T.failed` | any form, unexpected error | משהו השתבש. נסו שוב | placeholder |
| `T.personal` | bottom of every personal-page screen | הקישור הזה אישי. אל תשתפו אותו, שתפו רק את פסק הדין | placeholder |
| `T.waitingFor` | A's waiting page, title | בית המשפט ממתין לטענה של {name B} | placeholder |
| `T.timeLeft` | A's waiting page and B's form, countdown | נשארו {h:mm} שעות להגשה | placeholder |
| `T.sendToB` | A's waiting page, WhatsApp button | לשלוח לצד השני בוואטסאפ | placeholder |
| `T.nudgeB` | A's waiting page, WhatsApp button from 1 h | להציק שוב בוואטסאפ | placeholder |
| `T.invite` | WhatsApp message with B's link | 📜 הוגשה נגדך תביעה בבית המשפט העליון לענייני זבובים ⏎ התובע/ת: {name A} ⏎ בעניין: {topic} ⏎ יש לך 3 שעות להגיש טענה, לפני שהשופט נהיה רעב: {link} (no topic: no "בעניין" line) | placeholder → owner-approved |
| `T.nudgeText` | WhatsApp nudge message | תזכורת מבית המשפט: השופט עדיין מחכה לטענה שלך בתיק של {name A}, והבטן שלו כבר מקרקרת. נשארו {h:mm} שעות: {link} | placeholder → owner-approved |
| `T.summoned` | B's form, title | הוגשה נגדך תביעה מאת {name A} | placeholder → owner-approved |
| `T.submitB` | B's submit button | להגיש לזבוב | placeholder |
| `T.submitting` | B's submit button while sending | מגישים… | placeholder |
| `T.queued` | story, while waiting in line | התיק ממתין בתור. השופט מסיים דיון אחר… | placeholder |
| `T.enters` | story, first stage (verdict) | כל הקהל קם! כבוד השופט נכנס לאולם | placeholder → owner-approved |
| `T.entersAppeal` | story, first stage (appeal) | ערעור של {name}! השופט חוזר לאולם, לא מרוצה | placeholder → owner-approved |
| `T.tasting` | story, tasting stages | טועם את הטענה של {name}… | placeholder |
| `T.tastingWater` | story, B's tasting in a no-show | הנתבע לא התייצב. השופט טועם כוס מים… | placeholder → owner-approved |
| `T.deliberating` | story, last stage (cycles) | השופט משפשף את הרגליים… / מזמזם לעצמו בהתלבטות… / עוד רגע ההכרעה… | placeholder → owner-approved |
| `T.hungry` | story, after the mood line (wait ≥ 0.5 h) | השופט מחכה כבר {h} שעות, והבטן מקרקרת. | placeholder → owner-approved |
| `T.revealing` | story, live meter reveal | כמה הזבוב רצה לבלוע כל טענה… | placeholder |
| `T.water` | B's meter name in a no-show | כוס מים | placeholder |
| `T.appetite` | appetite meters | תיאבון | placeholder |
| `T.appealAcceptedBy` | verdict, above the headline (appeals) | הערעור של {name} התקבל! | placeholder |
| `T.appealRejectedBy` | verdict, above the headline (appeals) | הערעור של {name} נדחה | placeholder |
| `T.final` | verdict, after the history line | הפסק סופי | placeholder |
| `T.appeal` | verdict, appeal button | ערעור | placeholder |
| `T.appealing` | appeal button while sending | מגישים ערעור… | placeholder |
| `T.appealLeft` | verdict, under the appeal button | אפשר לערער עוד {h:mm} שעות | placeholder |
| `T.shareVerdict` | verdict, WhatsApp button | לשלוח את פסק הדין | placeholder |
| `T.shareText` | WhatsApp message with the public card | התיק: {topic} ⏎ {headline} ⏎ {link} | placeholder ("התיק:" part decided, SPEC §7) |
| `T.newCase` | verdict, notices, public card, /how | לפתוח תיק חדש | placeholder |
| `T.closed` | "case closed" page | התיק נסגר והועבר לארכיון. רוצים לפתוח תיק חדש? | placeholder → owner-approved; same as `views.CLOSED` |
| `T.ownLink` | A's device on B's link | זה הקישור של הצד השני. שלחו אותו אליו | placeholder; same as `views.OWN_LINK` |
| `T.taken` | another device on B's link after B submitted | התיק כבר בטיפול | decided (SPEC §3, §15.1); same as `views.TAKEN` |
| `T.notDecided` | public card before a verdict | הזבוב עוד לא פסק בתיק הזה | placeholder; same as `views.NOT_DECIDED`, `og.NOT_DECIDED` |
| `T.report` | public card, report button | דיווח על תוכן פוגעני | placeholder |
| `T.reportSure` | report button, after the first tap | בטוח? לחצו שוב כדי להסתיר את התיק | placeholder |
| `T.brain` | verdict, brain-view button | מה קרה במוח? | placeholder; same as `LAB.title` |
| `T.brainHide` | brain-view button when open | הסתר את המוח | placeholder |
| `T.brainLoading` | brain-view button while loading | פותחים את המוח… | placeholder |
| `T.how` | /how page title | איך זה עובד? | placeholder; same as the footer link |

## Mood and topic lines — `web/js/copy.js`

| Key | Where it appears | Current text | Status |
|---|---|---|---|
| `moodLine` | story, first stage | מצב השופט היום: {hunger word}, {irritability word}. | placeholder |
| `HUNGER` | hunger word in `moodLine` | שבע (< 0.25) / קצת רעב (< 0.5) / רעב (< 0.8) / מורעב | placeholder |
| `MOOD` | irritability word in `moodLine` | רגוע (< 0.15) / קצת עצבני (< 0.3) / עצבני | placeholder |
| `topicLine` | verdict, waiting pages, public card | התיק: {topic} | decided (SPEC §7) |

## Brain view — `web/js/copy.js` (`LAB`)

| Key | Where it appears | Current text | Status |
|---|---|---|---|
| `LAB.title` | brain view heading | מה קרה במוח? | placeholder; same as `T.brain` |
| `LAB.noAi` | brain view, under the heading | 140 אלף נוירונים של מוח זבוב אמיתי. בלי AI. | placeholder; same as the footer |
| `LAB.mn9` | MN9 chart heading | נוירון הבליעה (MN9) | placeholder |
| `LAB.mn9Hint` | under the chart heading | קצב הירי בזמן הטעימה (הרץ), ממוצע נע של רבע שנייה | placeholder |
| `LAB.at` | tap readout on the chart | {s} ש׳ · {name} {hz} הרץ · … | placeholder |
| `LAB.hz` | in the readout | {n} הרץ | placeholder |
| `LAB.seconds` | chart time axis | ש׳ | placeholder |
| `LAB.judge` | facts heading | מצב השופט | placeholder |
| `LAB.hunger` | facts | רעב | placeholder |
| `LAB.irritability` | facts | עצבנות | placeholder |
| `LAB.seed` | facts | זרע אקראי | placeholder |
| `LAB.version` | facts | גרסת סימולציה | placeholder |
| `LAB.platform` | facts | מחשב | placeholder |
| `LAB.error` | brain view failed to load | לא הצלחנו לפתוח את המוח. נסו שוב | placeholder |

## Public card — `web/js/public.js`

| Key | Where it appears | Current text | Status |
|---|---|---|---|
| `publicModel` names | public card, under the topic | {name A} נגד {name B} | placeholder; same as `og.card` names |

## How it works — `web/js/how.js` (`HOW`)

| Key | Where it appears | Current text | Status |
|---|---|---|---|
| `sections[0]` title | /how | מוח של זבוב אמיתי | placeholder |
| `sections[0]` text | /how | הבורר מריץ סימולציה של המוח השלם של זבוב הפירות: בערך 140 אלף נוירונים והקשרים ביניהם, כפי שמופו בפרויקט FlyWire מתוך צילומי מיקרוסקופ אלקטרונים. המודל בנוי כמו המודל של Shiu ועמיתיו (2024): כל נוירון צובר מתח ויורה, והקשרים מעבירים את הירי הלאה. | placeholder |
| `sections[1]` title | /how | מילים הופכות לטעמים | placeholder |
| `sections[1]` text | /how | כל טענה הופכת לאות טעם שמגיע לנוירוני חישת הטעם של הזבוב. כל טענה נטעמת לבד, באותה עוצמה משני צדי הפה. איך בדיוק מילים הופכות לטעמים נשאר סוד, כדי שאי אפשר יהיה לכתוב טענה מנצחת בכוונה. | placeholder |
| `sections[2]` title | /how | מי צודק | placeholder |
| `sections[2]` text | /how | בכל טעימה מקשיבים לנוירון אחד: MN9, שמפעיל את הבליעה. הטענה שהזבוב רצה לבלוע יותר מנצחת. מדי התיאבון בפסק הדין מראים בדיוק את זה. | placeholder |
| `sections[3]` title | /how | מצב הרוח של הזבוב | placeholder |
| `sections[3]` text | /how | מעל המוח האמיתי הוספנו שכבה משלנו, שלא באה מהמיפוי: רעב ועצבנות. הזבוב נעשה רעב יותר ככל שהצד השני מתעכב, ועצבנות מוסיפה רעש למוח. | placeholder |
| `sections[4]` title | /how | בלי AI | placeholder |
| `sections[4]` text | /how | אין כאן בינה מלאכותית ואין מודל שפה: לא בהכרעה, לא בנוסח פסק הדין ולא בסינון. רק נוירונים מדומים. אותו תיק, עם אותן טענות ואותו זרע אקראי, ייתן תמיד אותה תוצאה. | placeholder |
| `creditsTitle` | /how | קרדיטים | placeholder |
| `creditsIntro` | /how, above the credits | נתוני FlyWire (גרסה 783) משמשים לפי רישיון CC BY-NC 4.0. | placeholder (the credits themselves: SPEC §15.7) |

Note: a test fails if `/how` or the brain view contains a lone Hebrew
letter, a receptor group or a taste class (SPEC §2.3). Write "בערך 140",
not "כ־140".

## Verdict wording — `api/src/borer_api/verdicts.py` (sent by the API, shown by pages and previews)

| Key | Where it appears | Current text | Status |
|---|---|---|---|
| `HEADLINES["win"]` | verdict headline, public card, preview | פסק הדין: הצדק עם {name} | decided (SPEC §7) |
| `HEADLINES["dithered"]` | same | אחרי התלבטות קשה... הצדק עם {name} | decided (SPEC §7) |
| `HEADLINES["tie"]` | same | תיקו. הזבוב לא השתכנע מאף אחד | decided (SPEC §7) |
| `HEADLINES["froze"]` | same | הזבוב קפא. התיק הזה גדול עליו | decided (SPEC §7) |
| `HEADLINES["food"]` | same (lunch break) | הבורר יצא להפסקת צהריים. הדיון נדחה | decided (SPEC §7) |
| `PREFERRED_WATER` | no-show headline when water wins | הזבוב העדיף מים | decided (SPEC §8) |
| `NO_SHOW` | any other no-show headline | הצד השני לא התייצב לדיון | decided (SPEC §8) |
| `STEPS` | history line (verdict, public card, preview) | פסק דין / ערעור התקבל / ערעור נדחה, joined by " ← " (" · " in images) | placeholder (the sequence is SPEC §9) |

## API messages — `api/src/borer_api/views.py`

| Key | Where it appears | Current text | Status |
|---|---|---|---|
| `CLOSED` | every closed / wrong / expired / hidden link | התיק נסגר והועבר לארכיון. רוצים לפתוח תיק חדש? | placeholder → owner-approved; same as `T.closed` |
| `TAKEN` | B's link on another device after B submitted | התיק כבר בטיפול | decided (SPEC §15.1); same as `T.taken` |
| `OWN_LINK` | A's device on B's link | זה הקישור של הצד השני. שלחו אותו אליו | placeholder; same as `T.ownLink` |
| `LIMIT` | open-case form, 21st case of the day | הזבוב שמע מספיק תיקים מכם היום. נסו שוב מחר | placeholder |
| `LATE` | B's form after the deadline; B's link after a no-show | הזמן להגשת הטענה עבר | placeholder |
| `SUBMITTED` | B's form, submitted twice | הטענה כבר הוגשה | placeholder |
| `NOT_DECIDED` | appeal / brain / share before a verdict | הזבוב עוד לא פסק בתיק הזה | placeholder; same as `T.notDecided`, `og.NOT_DECIDED` |
| `APPEALED` | appeal, second time by the same side | כבר ערערת בתיק הזה | placeholder |
| `FINAL` | appeal after 3 hearings | הפסק סופי. אין עוד ערעורים בתיק הזה | placeholder |
| `APPEAL_LATE` | appeal after the 3 h window | עברו 3 שעות מפסק הדין. הפסק סופי | placeholder |
| `FAILED` | error state (the sim failed 3 times) | השופט התעלף באמצע הדיון. אפשר לפתוח תיק חדש | placeholder → owner-approved |

## Court — `api/src/borer_api/court.py`

| Key | Where it appears | Current text | Status |
|---|---|---|---|
| `BUSY` | submit / appeal when the court is full | הזבוב עסוק בתיקים אחרים כרגע. נסו שוב בעוד דקה | decided (SPEC §14.7) |

## Input rules — `api/src/borer_api/validate.py` (under the form fields)

| Key | Where it appears | Current text | Status |
|---|---|---|---|
| `SIDES` | inside the messages below | א׳ / ב׳ | placeholder |
| `BLOCKED` | any field with a listed word (soft block) | בית המשפט לא מקבל לשון כזו. נסחו את זה בנימוס | placeholder → owner-approved |
| topic too long | topic field | נושא התיק ארוך מדי (עד {80} תווים) | placeholder |
| name missing | name field | חסר שם לצד {א׳/ב׳} | placeholder |
| name too long | name field | השם של צד {א׳/ב׳} ארוך מדי (עד {30} תווים) | placeholder |
| argument too long | argument field | הטענה של צד {א׳/ב׳} ארוכה מדי (עד {280} תווים) | placeholder |
| argument too short | argument field | הטענה של צד {א׳/ב׳} צריכה לפחות {10} אותיות בעברית (יש {n}) | placeholder |

## Link previews — `api/src/borer_api/og.py` (WhatsApp tags and image lines)

| Key | Where it appears | Current text | Status |
|---|---|---|---|
| `SITE_TITLE` | preview title (start page, /how, A's link, closed) | הבורר | decided (name) |
| `SITE_TEXT` | preview description, same pages | יש ויכוח? זבוב אמיתי יכריע. 140 אלף נוירונים, בלי AI. | placeholder → owner-approved |
| `site()` image lines | site preview image | שני צדדים, זבוב אחד מכריע / בלי AI. רק מוח של זבוב. | placeholder |
| `teaser()` title | B's link preview title | הבורר · התיק: {topic} (no topic: הבורר · הוגשה נגדך תביעה) | placeholder → owner-approved |
| `teaser()` no-topic line | B's link preview, title and image | הוגשה נגדך תביעה | placeholder → owner-approved |
| `TEASER_TEXT` | B's link preview description and image | הוגשה נגדך תביעה. יש לך 3 שעות להתגונן. | placeholder → owner-approved |
| `NOT_DECIDED` | public card preview before a verdict | הזבוב עוד לא פסק בתיק הזה | placeholder; same as `views.NOT_DECIDED`, `T.notDecided` |
| `card()` names | public card preview | {name A} נגד {name B} | placeholder; same as `publicModel` names |
| `card()` topic | public card preview | התיק: {topic} | decided (SPEC §7) |

## Preview images — `api/src/borer_api/ogimage.py`

| Key | Where it appears | Current text | Status |
|---|---|---|---|
| header brand | every preview image | הבורר | decided (name) |
| header subtitle | every preview image | בית המשפט העליון לענייני זבובים | placeholder; same as the page header |
| `FOOTER` | every preview image | 140 אלף נוירונים של מוח זבוב אמיתי. בלי AI. | placeholder; same as the page footer, `LAB.noAi` |
