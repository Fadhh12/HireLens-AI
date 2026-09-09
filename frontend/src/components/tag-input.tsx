"use client";

import { useState, type KeyboardEvent } from "react";
import { XIcon } from "lucide-react";

import { Input } from "@/components/ui/input";

interface TagInputProps {
  value: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  id?: string;
}

/** Multi-add tag input (UI/UX Layar 4: "Skill wajib — tag input, multi-add").
 * Enter or comma commits the current text as a tag; click the × to remove one. */
export function TagInput({ value, onChange, placeholder, id }: TagInputProps) {
  const [draft, setDraft] = useState("");

  function commit() {
    const tag = draft.trim();
    if (tag && !value.includes(tag)) {
      onChange([...value, tag]);
    }
    setDraft("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      commit();
    } else if (e.key === "Backspace" && draft === "" && value.length > 0) {
      onChange(value.slice(0, -1));
    }
  }

  function removeTag(tag: string) {
    onChange(value.filter((t) => t !== tag));
  }

  return (
    <div className="border-input flex flex-wrap items-center gap-1.5 rounded-lg border bg-transparent p-1.5">
      {value.map((tag) => (
        <span
          key={tag}
          className="bg-secondary text-secondary-foreground flex items-center gap-1 rounded-md px-2 py-1 text-xs"
        >
          {tag}
          <button
            type="button"
            onClick={() => removeTag(tag)}
            className="hover:opacity-70"
            aria-label={`Hapus ${tag}`}
          >
            <XIcon className="size-3" />
          </button>
        </span>
      ))}
      <Input
        id={id}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={commit}
        placeholder={value.length === 0 ? placeholder : ""}
        className="h-7 min-w-32 flex-1 border-none px-1 shadow-none focus-visible:ring-0"
      />
    </div>
  );
}
