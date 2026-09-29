// Builds the interview deck. Run: node build_deck.js
const pptxgen = require("pptxgenjs");

const INK = "16203A";      // deep ink navy - dominant
const GROUND = "F7F7F5";   // off-white
const RED = "A81E14";      // blocked / danger
const GREEN = "1A6349";    // validated / passed
const SLATE = "4A5462";    // secondary text
const MUTE = "8A929E";     // captions
const LINE = "D8DCE3";
const ICE = "C9D4E8";      // light text on ink

const H = "Cambria";
const B = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
pres.author = "Factory Accident Support Bot";
pres.title = "Factory Accident Support Bot";

const M = 0.65;            // slide margin
const W = 13.33;

function label(slide, text, x, y, color) {
  slide.addText(text, {
    x, y, w: 6, h: 0.25, fontFace: B, fontSize: 10.5, bold: true,
    color: color || MUTE, charSpacing: 2, margin: 0,
  });
}

function title(slide, text, opts = {}) {
  slide.addText(text, {
    x: M, y: opts.y || 0.85, w: opts.w || 11.6, h: opts.h || 0.9,
    fontFace: H, fontSize: opts.size || 34, bold: true,
    color: opts.color || INK, margin: 0,
  });
}

// ---------------------------------------------------------------- 1. TITLE
{
  const s = pres.addSlide();
  s.background = { color: INK };

  label(s, "LUDHIANA, PUNJAB", M, 0.9, ICE);
  s.addText("Factory Accident\nSupport Bot", {
    x: M, y: 1.35, w: 7.3, h: 2.2, fontFace: H, fontSize: 46, bold: true,
    color: "FFFFFF", lineSpacing: 50, margin: 0,
  });
  s.addText(
    "A WhatsApp assistant for families of factory-accident victims, built so that it cannot be confidently wrong.",
    { x: M, y: 3.65, w: 6.9, h: 0.9, fontFace: B, fontSize: 15, color: ICE, margin: 0 }
  );

  s.addShape(pres.ShapeType.rect, {
    x: 8.35, y: 1.35, w: 4.3, h: 3.6, fill: { color: "1E2B4D" },
  });
  s.addText("“", {
    x: 8.65, y: 1.45, w: 1, h: 0.7, fontFace: H, fontSize: 40, color: RED, margin: 0,
  });
  s.addText(
    "In a legal crisis, a confidently wrong answer is worse than no answer.",
    { x: 8.7, y: 2.15, w: 3.6, h: 1.5, fontFace: H, fontSize: 19, italic: true,
      color: "FFFFFF", lineSpacing: 26, margin: 0 }
  );
  s.addText("The design rule everything else follows from", {
    x: 8.7, y: 3.95, w: 3.6, h: 0.6, fontFace: B, fontSize: 11, color: MUTE, margin: 0,
  });

  s.addText("Retrieval-gated RAG  ·  deterministic output validation  ·  human handoff", {
    x: M, y: 5.6, w: 11.6, h: 0.35, fontFace: B, fontSize: 12, color: ICE, margin: 0,
  });
  s.addNotes(
    "One line: I'm building a WhatsApp bot for families of factory-accident victims. " +
    "Most of the work has gone into stopping it from being confidently wrong, because " +
    "in a legal crisis that is worse than saying nothing."
  );
}

// ------------------------------------------------------------- 2. PROBLEM
{
  const s = pres.addSlide();
  s.background = { color: GROUND };
  label(s, "THE SITUATION", M, 0.5);
  title(s, "The first 72 hours decide the claim");

  s.addText(
    [
      { text: "A worker dies on a factory floor in Ludhiana. In the days that follow, his family must secure a post-mortem, get an FIR registered and refuse the settlement they are offered at the gate.", options: { breakLine: true, paraSpaceAfter: 10 } },
      { text: "They are grieving, often not literate in English and getting advice from whoever is nearby. A wrong figure or a wrong office costs them months they do not have, or the entire claim.", options: {} },
    ],
    { x: M, y: 2.0, w: 6.4, h: 2.4, fontFace: B, fontSize: 15, color: SLATE, lineSpacing: 23, margin: 0 }
  );

  const stats = [
    ["2 years", "Hard deadline to file a compensation claim from the date of death", INK],
    ["Hours", "The window to insist on a post-mortem before evidence is lost", RED],
    ["Full & final", "The wording on the paper a widow is asked to sign at the factory gate", RED],
  ];
  stats.forEach(([big, small, col], i) => {
    const y = 1.95 + i * 1.35;
    s.addShape(pres.ShapeType.rect, {
      x: 7.5, y, w: 5.15, h: 1.15, fill: { color: "FFFFFF" }, line: { color: LINE, width: 1 },
    });
    s.addText(big, {
      x: 7.75, y: y + 0.12, w: 2.0, h: 0.5, fontFace: H, fontSize: 22, bold: true, color: col, margin: 0,
    });
    s.addText(small, {
      x: 7.75, y: y + 0.6, w: 4.65, h: 0.5, fontFace: B, fontSize: 11.5, color: SLATE, margin: 0,
    });
  });
  s.addNotes("Set the stakes before any technology. The audience needs to feel why a wrong answer here is not a cosmetic bug.");
}

// ------------------------------------------------- 3. WHY A BOT IS RISKY
{
  const s = pres.addSlide();
  s.background = { color: GROUND };
  label(s, "THE CORE PROBLEM", M, 0.5);
  title(s, "The obvious safety mechanisms do not work");

  const rows = [
    ["A similarity score cannot tell scope", "An off-topic question about the weather scored 0.653, higher than three legitimate questions, including “how much exactly will we get” at 0.598. The bands are inverted, so no threshold separates them."],
    ["A high score can be a repealed statute", "The Factories Act 1948 chunk is genuinely the most relevant text for “what must the factory do”. It is simply no longer law. Similarity has no opinion about that."],
    ["A safety rule in a prompt is a request", "Told not to invent contact details, the model complied most of the time, which is the worst possible reliability profile, because it looks fine in testing."],
  ];
  rows.forEach(([head, body], i) => {
    const y = 1.95 + i * 1.5;
    s.addShape(pres.ShapeType.ellipse, {
      x: M, y: y + 0.05, w: 0.42, h: 0.42, fill: { color: RED },
    });
    s.addText(String(i + 1), {
      x: M, y: y + 0.05, w: 0.42, h: 0.42, fontFace: B, fontSize: 14, bold: true,
      color: "FFFFFF", align: "center", valign: "middle", margin: 0,
    });
    s.addText(head, {
      x: 1.3, y, w: 11.3, h: 0.4, fontFace: H, fontSize: 19, bold: true, color: INK, margin: 0,
    });
    s.addText(body, {
      x: 1.3, y: y + 0.42, w: 11.2, h: 0.85, fontFace: B, fontSize: 13.5, color: SLATE,
      lineSpacing: 20, margin: 0,
    });
  });
  s.addNotes("Each of these was found by measurement, not assumption. That is the argument of the whole project.");
}

// ------------------------------------------------------ 4. SOURCE AUDIT
{
  const s = pres.addSlide();
  s.background = { color: GROUND };
  label(s, "BEFORE BUILDING ANYTHING", M, 0.5);
  title(s, "I checked the sources. Most were unusable.");

  const cards = [
    ["2 of 5 sources were dead law", "The Factories Act 1948 and the Employees' Compensation Act 1923 were both repealed on 21 Nov 2025 and replaced by the new labour codes."],
    ["One file was not the Act at all", "It was a two-page FAQ with obsolete figures that omitted factory workers from its coverage list. A bot using it could have told a factory widow she was not covered."],
    ["The FIR source was a blog post", "It cited five repealed CrPC and IPC sections, including the exact police-escalation step the product promises."],
    ["The most urgent provision was missing", "s.194 BNSS, which governs the inquest and post-mortem after a factory death, appeared nowhere in the collected material."],
  ];
  cards.forEach(([head, body], i) => {
    const x = M + (i % 2) * 6.15;
    const y = 1.95 + Math.floor(i / 2) * 2.15;
    s.addShape(pres.ShapeType.rect, {
      x, y, w: 5.85, h: 1.9, fill: { color: "FFFFFF" }, line: { color: LINE, width: 1 },
    });
    s.addText(head, {
      x: x + 0.3, y: y + 0.22, w: 5.25, h: 0.55, fontFace: H, fontSize: 17, bold: true,
      color: RED, margin: 0,
    });
    s.addText(body, {
      x: x + 0.3, y: y + 0.75, w: 5.25, h: 1.0, fontFace: B, fontSize: 12.5, color: SLATE,
      lineSpacing: 18, margin: 0,
    });
  });

  s.addText("Had I skipped this step, the bot would have cited repealed statutes to grieving families, fluently.", {
    x: M, y: 6.35, w: 11.6, h: 0.4, fontFace: H, fontSize: 15, italic: true, color: INK, margin: 0,
  });
  s.addNotes("This is the slide that shows judgement rather than effort. The knowledge base was rebuilt from gazette texts: 28 verified chunks, current law only.");
}

// ------------------------------------------------------ 5. ARCHITECTURE
{
  const s = pres.addSlide();
  s.background = { color: GROUND };
  label(s, "ARCHITECTURE", M, 0.5);
  title(s, "Order of operations is the safety design");

  const steps = [
    ["Intent", "Keyword, then\nclassifier", INK],
    ["Retrieve", "Top-K from\n28 chunks", INK],
    ["Metadata gate", "Legal status\nbefore similarity", RED],
    ["Threshold", "A floor, not a\nrelevance test", INK],
    ["Answer model", "Only verified law\nin context", INK],
    ["Validator", "Checked before\nit is sent", GREEN],
  ];
  const bw = 1.87, gap = 0.13;
  steps.forEach(([head, body, col], i) => {
    const x = M + i * (bw + gap);
    s.addShape(pres.ShapeType.roundRect, {
      x, y: 2.1, w: bw, h: 1.5, rectRadius: 0.06,
      fill: { color: "FFFFFF" }, line: { color: col, width: col === INK ? 1 : 2 },
    });
    s.addText(head, {
      x, y: 2.28, w: bw, h: 0.35, fontFace: H, fontSize: 14, bold: true,
      color: col, align: "center", margin: 0,
    });
    s.addText(body, {
      x, y: 2.68, w: bw, h: 0.8, fontFace: B, fontSize: 10.5, color: SLATE,
      align: "center", lineSpacing: 14, margin: 0,
    });
    if (i < steps.length - 1) {
      s.addText("›", {
        x: x + bw, y: 2.55, w: gap, h: 0.5, fontFace: B, fontSize: 18, bold: true,
        color: MUTE, align: "center", margin: 0,
      });
    }
  });

  const notes = [
    ["Settlement pressure never reaches retrieval", "A signature cannot be un-signed, so that intent is caught by an offline keyword check and answered with pre-approved text. No model is called."],
    ["Repealed law is dropped before similarity is considered", "A chunk that is genuinely relevant but no longer law is removed by rule, not by score."],
    ["Contact details never pass through the model", "Verified numbers are appended by code after validation, so the model cannot invent or corrupt one."],
  ];
  notes.forEach(([head, body], i) => {
    const y = 4.15 + i * 0.92;
    s.addText(head, {
      x: M, y, w: 11.6, h: 0.32, fontFace: H, fontSize: 14, bold: true, color: INK, margin: 0,
    });
    s.addText(body, {
      x: M, y: y + 0.32, w: 11.6, h: 0.5, fontFace: B, fontSize: 12.5, color: SLATE, margin: 0,
    });
  });
  s.addNotes("The threshold sits after the gates so a repealed-but-relevant chunk cannot score its way past, and before the model so a weak context is never drafted from.");
}

// ------------------------------------------- 6. LAW BEFORE SIMILARITY
{
  const s = pres.addSlide();
  s.background = { color: GROUND };
  label(s, "THE MEASUREMENT", M, 0.5);
  title(s, "Ranked first. Dropped anyway.");

  s.addText("0.786", {
    x: M, y: 1.9, w: 4.2, h: 1.4, fontFace: H, fontSize: 72, bold: true, color: RED, margin: 0,
  });
  s.addText("Similarity of the repealed Factories Act chunk: rank #1, the highest score in the entire test suite.", {
    x: M, y: 3.25, w: 4.3, h: 1.1, fontFace: B, fontSize: 13.5, color: SLATE, lineSpacing: 20, margin: 0,
  });
  s.addText("The gate dropped it, and the question was then answered correctly from the current Code.", {
    x: M, y: 4.45, w: 4.3, h: 1.0, fontFace: H, fontSize: 14, italic: true, color: INK, lineSpacing: 20, margin: 0,
  });

  const ranks = [
    ["1", "0.786", "Factories Act 1948", "REPEALED, DROPPED", RED],
    ["2", "0.775", "OSHWC Code 2020: which law applies now", "in force", GREEN],
    ["3", "0.761", "OSHWC Code 2020: employer safety duty", "in force", GREEN],
    ["4", "0.731", "OSHWC Code 2020: duty to notify a death", "in force", GREEN],
    ["5", "0.715", "Social Security Code 2020: s.74 liability", "in force", GREEN],
  ];
  s.addText("RETRIEVED FOR “what does the Factories Act say the factory must do”", {
    x: 5.35, y: 1.9, w: 7.3, h: 0.3, fontFace: B, fontSize: 10.5, bold: true, color: MUTE,
    charSpacing: 1, margin: 0,
  });
  ranks.forEach(([n, score, name, state, col], i) => {
    const y = 2.35 + i * 0.72;
    s.addShape(pres.ShapeType.rect, {
      x: 5.35, y, w: 7.3, h: 0.62,
      fill: { color: i === 0 ? "FBEAE8" : "FFFFFF" }, line: { color: LINE, width: 1 },
    });
    s.addText(n, {
      x: 5.5, y, w: 0.35, h: 0.62, fontFace: B, fontSize: 12, bold: true, color: MUTE,
      valign: "middle", margin: 0,
    });
    s.addText(score, {
      x: 5.9, y, w: 0.85, h: 0.62, fontFace: B, fontSize: 13, bold: true, color: col,
      valign: "middle", margin: 0,
    });
    s.addText(name, {
      x: 6.8, y, w: 4.0, h: 0.62, fontFace: B, fontSize: 11.5, color: INK, valign: "middle", margin: 0,
    });
    s.addText(state, {
      x: 10.85, y, w: 1.7, h: 0.62, fontFace: B, fontSize: 9.5, bold: i === 0, color: col,
      valign: "middle", align: "right", margin: 0,
    });
  });
  s.addNotes("Normal RAG ranks by similarity. That fails here, because a repealed law is genuinely relevant. It is just not law any more. So legal status is filtered before similarity is considered at all.");
}

// -------------------------------------------------- 7. BEFORE / AFTER
{
  const s = pres.addSlide();
  s.background = { color: GROUND };
  label(s, "MAKING IT SPEAK", M, 0.5);
  title(s, "Good answers, and an invented helpline");

  const cols = [
    ["Safety rules in the prompt", RED, "FBEAE8", [
      "Invented contact details in 3 of 6 answers, including a fake legal aid helpline number",
      "Stated a rupee figure the prompt had explicitly forbidden",
      "Answers ran 165–268 words, far past what a grieving reader can hold",
      "Complied most of the time, which looks fine in testing",
    ]],
    ["A validator that runs before sending", GREEN, "E6F2ED", [
      "Zero fabricated contacts. Verified numbers are appended by code, never generated",
      "Every figure must appear verbatim in the retrieved law, so a computed number cannot pass",
      "Every section citation grounded the same way",
      "Every refusal logged as evidence of a gap in the knowledge base",
    ]],
  ];
  cols.forEach(([head, col, tint, items], i) => {
    const x = M + i * 6.15;
    s.addShape(pres.ShapeType.rect, {
      x, y: 1.95, w: 5.85, h: 0.62, fill: { color: tint },
    });
    s.addText(head, {
      x: x + 0.25, y: 1.95, w: 5.35, h: 0.62, fontFace: H, fontSize: 16, bold: true,
      color: col, valign: "middle", margin: 0,
    });
    s.addText(
      items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < items.length - 1, paraSpaceAfter: 9 } })),
      { x: x + 0.25, y: 2.75, w: 5.35, h: 2.5, fontFace: B, fontSize: 12.5, color: SLATE, lineSpacing: 18, margin: 0 }
    );
  });

  s.addShape(pres.ShapeType.rect, {
    x: M, y: 5.55, w: 12.0, h: 1.1, fill: { color: "FFFFFF" }, line: { color: LINE, width: 1 },
  });
  s.addText("The validator refused one correct answer, and that was the useful result.", {
    x: M + 0.3, y: 5.68, w: 11.4, h: 0.3, fontFace: H, fontSize: 14, bold: true, color: INK, margin: 0,
  });
  s.addText("The Code writes “fifty per cent.” in words; the model wrote “50 %” in numerals; the check compares literally. One case passed by writing “half”, another was withheld for writing the same fact in digits, so which answer a family got was a coin flip on phrasing. Fixed in the source text, not by weakening the check.", {
    x: M + 0.3, y: 5.98, w: 11.4, h: 0.6, fontFace: B, fontSize: 11.5, color: SLATE, lineSpacing: 16, margin: 0,
  });
  s.addNotes("Most students only show the version that works. The interesting part is the refusal, and why relaxing the validator would have been the wrong fix.");
}

// ------------------------------------------------------- 8. LIVE RESULTS
{
  const s = pres.addSlide();
  s.background = { color: GROUND };
  label(s, "RUNNING NOW", M, 0.5);
  title(s, "Eight cases, end to end");

  const rows = [
    ["“my husband died, what are we owed?”", "answered from s.76", "PASS", GREEN],
    ["“how much money will we get exactly?”", "explains method, no total", "PASS", GREEN],
    ["“the police are refusing to write the FIR”", "s.173(4) BNSS escalation", "PASS", GREEN],
    ["“they took his body away”", "s.194 BNSS post-mortem", "PASS", GREEN],
    ["“the owner is offering 2 lakh to sign”", "pre-approved text, no model call", "PRE-EMPTED", INK],
    ["“he worked through a thekedar”", "s.85 principal-employer liability", "PASS", GREEN],
    ["“what is the weather in Ludhiana”", "never reaches retrieval or the model", "OUT OF SCOPE", INK],
    ["“what does the Factories Act say”", "repealed chunk dropped, answered from OSHWC", "PASS", GREEN],
  ];
  rows.forEach(([q, outcome, tag, col], i) => {
    const y = 1.95 + i * 0.55;
    s.addShape(pres.ShapeType.rect, {
      x: M, y, w: 8.6, h: 0.5, fill: { color: i % 2 ? "FFFFFF" : "EFF1F4" },
    });
    s.addText(q, {
      x: M + 0.2, y, w: 4.0, h: 0.5, fontFace: B, fontSize: 11.5, color: INK, valign: "middle", margin: 0,
    });
    s.addText(outcome, {
      x: M + 4.25, y, w: 4.15, h: 0.5, fontFace: B, fontSize: 11, color: SLATE, valign: "middle", margin: 0,
    });
    s.addText(tag, {
      x: 9.38, y, w: 1.4, h: 0.5, fontFace: B, fontSize: 9.5, bold: true, color: col, valign: "middle", margin: 0,
    });
  });

  const kpis = [["8 / 8", "cases behave as specified"], ["22 / 22", "intent routing, zero misroutes"], ["0", "fabricated contacts"], ["87–144", "words per answer, from 165–268"]];
  kpis.forEach(([big, small], i) => {
    const y = 1.95 + i * 1.1;
    s.addText(big, {
      x: 10.95, y, w: 1.8, h: 0.5, fontFace: H, fontSize: 24, bold: true, color: INK, margin: 0,
    });
    s.addText(small, {
      x: 10.95, y: y + 0.46, w: 1.85, h: 0.55, fontFace: B, fontSize: 10, color: SLATE, lineSpacing: 13, margin: 0,
    });
  });
  s.addNotes("Live demo goes here. Open the web client and send case 4 and case 7: the post-mortem answer, then the weather question that never reaches the model.");
}

// --------------------------------------------------- 9. WHAT IS OFF
{
  const s = pres.addSlide();
  s.background = { color: GROUND };
  label(s, "DELIBERATELY SWITCHED OFF", M, 0.5);
  title(s, "What it refuses to do, and why");

  const items = [
    ["The compensation calculator", "The Code sets the death formula as 50% of monthly wages multiplied by an age factor, but delegates both the minimum amount and the wage ceiling to Central Government notifications that are not in the Act. Until those are located, the bot explains how the amount is worked out and refuses to state a total. Enforced in code, not by instruction."],
    ["Citing the settlement provision", "The old blanket protection was repealed. The new Code protects families by a different mechanism, and a legal partner must confirm which provision applies before the bot cites anything."],
    ["Answering in Punjabi", "Speech input works today. Machine-translating a verified legal answer would put text in front of a family that passed none of the checks the English answer passed."],
  ];
  items.forEach(([head, body], i) => {
    const y = 1.95 + i * 1.55;
    s.addShape(pres.ShapeType.rect, {
      x: M, y, w: 12.0, h: 1.35, fill: { color: "FFFFFF" }, line: { color: LINE, width: 1 },
    });
    s.addShape(pres.ShapeType.ellipse, {
      x: M + 0.3, y: y + 0.45, w: 0.4, h: 0.4, fill: { color: INK },
    });
    s.addText("!", {
      x: M + 0.3, y: y + 0.45, w: 0.4, h: 0.4, fontFace: B, fontSize: 15, bold: true,
      color: "FFFFFF", align: "center", valign: "middle", margin: 0,
    });
    s.addText(head, {
      x: M + 0.95, y: y + 0.18, w: 10.9, h: 0.35, fontFace: H, fontSize: 16, bold: true, color: INK, margin: 0,
    });
    s.addText(body, {
      x: M + 0.95, y: y + 0.52, w: 10.9, h: 0.72, fontFace: B, fontSize: 12, color: SLATE,
      lineSpacing: 17, margin: 0,
    });
  });
  s.addNotes("Refusing well is a feature here. Each of these is a decision a lawyer has to make, not one I can make.");
}

// --------------------------------------------------- 10. ROADMAP / CLOSE
{
  const s = pres.addSlide();
  s.background = { color: INK };
  label(s, "WHAT COMES NEXT", M, 0.75, ICE);
  s.addText("Roadmap", {
    x: M, y: 1.15, w: 8, h: 0.8, fontFace: H, fontSize: 34, bold: true, color: "FFFFFF", margin: 0,
  });

  const road = [
    ["Legal partner sign-off", "Two Central Government notifications, and the settlement wording. Nothing reaches a real family before this."],
    ["WhatsApp delivery", "Webhook, signature verification and rate limiting are built and tested. A trial account cannot send free-form messages; the upgrade is the only blocker."],
    ["Voice in Hindi and Punjabi", "Speech-to-text is available on the existing stack. Speech output waits for a translator a lawyer trusts."],
    ["Union-led distribution", "The families who need this do not search for it. CITU and HMS reach them; a legal-aid partner gives the answers authority."],
  ];
  road.forEach(([head, body], i) => {
    const x = M + (i % 2) * 6.15;
    const y = 2.2 + Math.floor(i / 2) * 1.6;
    s.addShape(pres.ShapeType.rect, {
      x, y, w: 5.85, h: 1.35, fill: { color: "1E2B4D" },
    });
    s.addText(head, {
      x: x + 0.3, y: y + 0.15, w: 5.25, h: 0.35, fontFace: H, fontSize: 15, bold: true,
      color: "FFFFFF", margin: 0,
    });
    s.addText(body, {
      x: x + 0.3, y: y + 0.5, w: 5.25, h: 0.75, fontFace: B, fontSize: 11.5, color: ICE,
      lineSpacing: 16, margin: 0,
    });
  });

  s.addText("The interesting problem was never building a chatbot. It was discovering that the obvious safety mechanisms don't work, and replacing each one with something deterministic.", {
    x: M, y: 5.75, w: 12.0, h: 1.0, fontFace: H, fontSize: 17, italic: true, color: "FFFFFF",
    lineSpacing: 26, margin: 0,
  });
  s.addNotes(
    "Expect two questions. How do you ensure legal accuracy: curated corpus from gazette texts, gates on legal status, a deterministic validator and human handoff when uncertain. " +
    "How would this scale: a legal content partner, union-driven trust and CSR or small-grant funding."
  );
}

pres.writeFile({ fileName: "Factory_Accident_Support_Bot.pptx" })
  .then(f => console.log("wrote", f));
