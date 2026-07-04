"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useWorkspace } from "@/lib/workspace-context";

export function useGlobalKeyboard() {
  const router = useRouter();
  const { toggleSidebar } = useWorkspace();

  useEffect(() => {
    function handler(e: KeyboardEvent) {
      const isCtrl = e.metaKey || e.ctrlKey;
      const isShift = e.shiftKey;

      // Don't capture standard keys when editing in inputs, textareas or Monaco Editor
      const target = e.target as HTMLElement;
      const isEditing =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable ||
        target.className.includes("input") ||
        target.className.includes("textarea") ||
        target.className.includes("monaco");

      // Global shortcuts
      if (isCtrl) {
        if (e.key === "\\") {
          e.preventDefault();
          toggleSidebar();
          return;
        }

        // Only block editing behavior for structural shortcuts
        if (isEditing) return;

        if (e.key === "1") {
          e.preventDefault();
          router.push("/");
          return;
        }
        if (e.key === "2") {
          e.preventDefault();
          router.push("/contexts");
          return;
        }
        if (e.key === "3") {
          e.preventDefault();
          router.push("/templates");
          return;
        }
        if (e.key === "4") {
          e.preventDefault();
          router.push("/conversations");
          return;
        }
      }
    }

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [router, toggleSidebar]);
}
