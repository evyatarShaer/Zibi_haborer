// "How it works" (SPEC §15.7), at /how: a general explanation and the credits CC-BY-NC
// requires (checked 2026-10-26 against FlyWire's citation table). Group-level only: no
// letter, receptor group or taste class appears here (SPEC §2.3; checked by a test).
// The Hebrew text is placeholder copy for the owner.
import { el, show } from "./dom.js";
import { T } from "./copy.js";

export const HOW = {
  sections: [
    ["מוח של זבוב אמיתי",
      "הבורר מריץ סימולציה של המוח השלם של זבוב הפירות: בערך 140 אלף נוירונים והקשרים ביניהם, כפי " +
      "שמופו בפרויקט FlyWire מתוך צילומי מיקרוסקופ אלקטרונים. המודל בנוי כמו המודל של Shiu ועמיתיו " +
      "(2024): כל נוירון צובר מתח ויורה, והקשרים מעבירים את הירי הלאה."],
    ["מילים הופכות לטעמים",
      "כל טענה הופכת לאות טעם שמגיע לנוירוני חישת הטעם של הזבוב. כל טענה נטעמת לבד, באותה עוצמה " +
      "משני צדי הפה. איך בדיוק מילים הופכות לטעמים נשאר סוד, כדי שאי אפשר יהיה לכתוב טענה מנצחת בכוונה."],
    ["מי צודק",
      "בכל טעימה מקשיבים לנוירון אחד: MN9, שמפעיל את הבליעה. הטענה שהזבוב רצה לבלוע יותר מנצחת. " +
      "מדי התיאבון בפסק הדין מראים בדיוק את זה."],
    ["מצב הרוח של הזבוב",
      "מעל המוח האמיתי הוספנו שכבה משלנו, שלא באה מהמיפוי: רעב ועצבנות. הזבוב נעשה רעב יותר ככל " +
      "שהצד השני מתעכב, ועצבנות מוסיפה רעש למוח."],
    ["בלי AI",
      "אין כאן בינה מלאכותית ואין מודל שפה: לא בהכרעה, לא בנוסח פסק הדין ולא בסינון. רק נוירונים " +
      "מדומים. אותו תיק, עם אותן טענות ואותו זרע אקראי, ייתן תמיד אותה תוצאה."],
  ],
  creditsTitle: "קרדיטים",
  creditsIntro: "נתוני FlyWire (גרסה 783) משמשים לפי רישיון CC BY-NC 4.0.",
  credits: [
    ["Dorkenwald et al. 2024", "FlyWire connectome", "10.1038/s41586-024-07558-y"],
    ["Schlegel et al. 2024", "FlyWire annotation and cell types", "10.1038/s41586-024-07686-5"],
    ["Zheng et al. 2018", "FAFB electron microscopy volume", "10.1016/j.cell.2018.06.019"],
    ["Buhmann et al. 2021", "synapses (v783)", "10.1038/s41592-021-01183-7"],
    ["Heinrich et al. 2018", "synapses (v783)", "10.1007/978-3-030-00934-2_36"],
    ["Eckstein, Bates et al. 2024", "neurotransmitter predictions", "10.1016/j.cell.2024.03.016"],
    ["Shiu et al. 2024", "the whole-brain model", "10.1038/s41586-024-07763-9"],
  ],
};

export function howPage(root) {
  show(root, el("section", { class: "card how" },
    el("h2", {}, T.how),
    HOW.sections.map(([title, text]) => [el("h3", {}, title), el("p", {}, text)]),
    el("h3", {}, HOW.creditsTitle), el("p", {}, HOW.creditsIntro),
    el("ul", { class: "credits", dir: "ltr" }, HOW.credits.map(([who, what, doi]) =>
      el("li", {}, `${who}, ${what}. `, el("a", { href: `https://doi.org/${doi}`,
        target: "_blank", rel: "noopener" }, `doi:${doi}`)))),
    el("a", { class: "button primary", href: "/" }, T.newCase)));
}
