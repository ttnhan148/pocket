import { describe, it, expect } from "vitest";
import { cn } from "./utils";

describe("cn class merger utility", () => {
  it("should merge tailwind classes correctly", () => {
    const result = cn("text-red-500", "bg-blue-500");
    expect(result).toContain("text-red-500");
    expect(result).toContain("bg-blue-500");
  });

  it("should override conflicting tailwind classes correctly", () => {
    const result = cn("p-4", "p-6");
    expect(result).toBe("p-6");
  });

  it("should handle conditional classes", () => {
    const result = cn("text-red-500", false && "bg-blue-500", true && "font-bold");
    expect(result).toContain("text-red-500");
    expect(result).not.toContain("bg-blue-500");
    expect(result).toContain("font-bold");
  });
});
