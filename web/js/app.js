// Router by path (SPEC §15.1): "/" opens a case (A); "/a/{token}" and "/b/{token}" are the
// two personal pages; "/c/{case id}" is the public share card; "/how" explains it all.
// The header's tools (how it works, day / night) are filled in here.
import { casePage } from "./casepage.js";
import { howPage } from "./how.js";
import { icon } from "./icons.js";
import { openCaseScreen } from "./input.js";
import { publicPage } from "./public.js";
import { themeToggle } from "./theme.js";

const root = document.getElementById("app");
document.querySelector(".how-link").append(icon("help"));
document.querySelector(".tools").append(themeToggle());
const m = location.pathname.match(/^\/([abc])\/([\w-]+)\/?$/);
if (location.pathname === "/how") howPage(root);
else if (!m) openCaseScreen(root);
else if (m[1] === "c") publicPage(root, m[2]);
else casePage(root, m[1], m[2]);
