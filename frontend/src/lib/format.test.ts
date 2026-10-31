import { describe, expect, it } from "vitest";
import { formatDate, safeHttpUrl } from "./format";

describe("formatDate", () => {
  it("keeps only the date part of an ISO timestamp", () => {
    expect(formatDate("2026-07-08T09:00:00+09:00")).toBe("2026-07-08");
    expect(formatDate("2026-07-08")).toBe("2026-07-08");
  });
});

describe("safeHttpUrl", () => {
  it("allows http and https links", () => {
    expect(safeHttpUrl("https://www.hankyung.com/a")).toBe("https://www.hankyung.com/a");
    expect(safeHttpUrl("http://example.com/x")).toBe("http://example.com/x");
  });

  it("rejects script and malformed links", () => {
    expect(safeHttpUrl("javascript:alert(1)")).toBeNull();
    expect(safeHttpUrl("not a url")).toBeNull();
  });
});
