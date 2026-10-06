import { useLayoutEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

// Long free-text descriptions would push the important info (dates, votes, attendees) far down
// the page, so they are cut to a few lines with a "show more" toggle. The toggle only shows up
// when the text actually overflows. The line count lives in App.css (.expandable-text.collapsed).
export default function ExpandableText({ text }: { text: string }) {
  const { t } = useTranslation();
  const textRef = useRef<HTMLParagraphElement>(null);
  const [expanded, setExpanded] = useState(false);
  const [overflowing, setOverflowing] = useState(false);

  useLayoutEffect(() => {
    const el = textRef.current;
    if (!el || expanded) return;
    const measure = () => setOverflowing(el.scrollHeight > el.clientHeight + 1);
    measure();
    // The width decides how many lines the text wraps into, so re-measure on resize.
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => observer.disconnect();
  }, [text, expanded]);

  const collapsed = !expanded;
  return (
    <div className="expandable-text-wrap">
      <p
        ref={textRef}
        className={[
          "multiline-text",
          "expandable-text",
          collapsed && "collapsed",
          collapsed && overflowing && "fade",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {text}
      </p>
      {overflowing && (
        <button
          type="button"
          className="expand-toggle"
          aria-expanded={expanded}
          onClick={() => setExpanded((prev) => !prev)}
        >
          {t(expanded ? "common.showLess" : "common.showMore")}
        </button>
      )}
    </div>
  );
}
