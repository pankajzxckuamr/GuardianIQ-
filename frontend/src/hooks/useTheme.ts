/* src/hooks/useTheme.ts */
import { useEffect, useState } from "react";

export function useTheme() {
  const [theme] = useState<"dark">("dark");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  return { theme };
}
