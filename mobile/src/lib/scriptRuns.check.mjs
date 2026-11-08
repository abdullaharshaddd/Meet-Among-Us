// Run with: node src/lib/scriptRuns.check.mjs
import assert from "node:assert/strict";
import { guessDirection, splitRuns } from "./scriptRuns.ts";

assert.deepEqual(splitRuns("Weekly sync"), [{ text: "Weekly sync", isUrdu: false }]);

assert.deepEqual(splitRuns("آج کی میٹنگ"), [{ text: "آج کی میٹنگ", isUrdu: true }]);

const mixed = splitRuns("Kal ki meeting mein launch date final hui — ہم نے Thursday 15:00 رکھا");
assert.deepEqual(
  mixed.map((run) => [run.text, run.isUrdu]),
  [
    ["Kal ki meeting mein launch date final hui — ", false],
    ["ہم نے", true],
    [" Thursday 15:00 ", false],
    ["رکھا", true],
  ],
);

assert.equal(splitRuns("ٹھیک ہے۔")[0].text, "ٹھیک ہے۔");
assert.deepEqual(splitRuns(""), []);

assert.equal(guessDirection("Sprint ka review ہم نے کل کیا"), "rtl");
assert.equal(guessDirection("Ok تو phir ہم Thursday کو ملتے ہیں"), "rtl");
assert.equal(guessDirection("Ali نے 3 tasks لیے"), "rtl"); // 2 v 2, tie goes to rtl
assert.equal(guessDirection("نے Ali لیے tasks"), "rtl"); // 2 v 2, Urdu first
assert.equal(guessDirection("We decided ہم نے, then moved on"), "ltr"); // 2 v 3
assert.equal(guessDirection("We decided ہم نے"), "rtl"); // 2 v 2
assert.equal(guessDirection("میٹنگ 15:00 بجے شروع ہوئی"), "rtl");
assert.equal(guessDirection("15:00"), "ltr");

console.log("scriptRuns: all checks passed");
