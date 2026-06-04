/* src/utils/dates.ts */

export function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return "—";
  try {
    // If the date string has a 'T' but no timezone offset/Z, append 'Z' to parse as UTC
    let normalizedDateStr = dateStr;
    if (dateStr.includes("T") && !dateStr.endsWith("Z") && !/[+-]\d{2}:?\d{2}$/.test(dateStr)) {
      normalizedDateStr = dateStr + "Z";
    }
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
      timeZone: "Asia/Kolkata",
    }).format(new Date(normalizedDateStr));
  } catch {
    return dateStr;
  }
}

export function timeAgo(dateStr: string): string {
  const now = Date.now();
  let normalizedDateStr = dateStr;
  if (dateStr.includes("T") && !dateStr.endsWith("Z") && !/[+-]\d{2}:?\d{2}$/.test(dateStr)) {
    normalizedDateStr = dateStr + "Z";
  }
  const then = new Date(normalizedDateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}
