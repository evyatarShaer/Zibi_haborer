// Router by path (SPEC §15.1): "/" opens a case (A); "/a/{token}" and "/b/{token}" are the
// two personal pages; "/c/{case id}" is the public share card.
import { casePage } from "./casepage.js";
import { openCaseScreen } from "./input.js";
import { publicPage } from "./public.js";

const root = document.getElementById("app");
const m = location.pathname.match(/^\/([abc])\/([\w-]+)\/?$/);
if (!m) openCaseScreen(root);
else if (m[1] === "c") publicPage(root, m[2]);
else casePage(root, m[1], m[2]);
