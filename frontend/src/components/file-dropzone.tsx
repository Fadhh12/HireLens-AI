"use client";

import { useRef, useState, type DragEvent } from "react";
import { FileIcon, UploadIcon, XIcon } from "lucide-react";

interface FileDropzoneProps {
  label: string;
  accept: string;
  hint: string;
  multiple?: boolean;
  files: File[];
  onChange: (files: File[]) => void;
}

/** Drag-and-drop upload zone (UI/UX Layar 5). */
export function FileDropzone({ label, accept, hint, multiple, files, onChange }: FileDropzoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function addFiles(list: FileList | null) {
    if (!list) return;
    const incoming = Array.from(list);
    onChange(multiple ? [...files, ...incoming] : incoming.slice(0, 1));
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    addFiles(e.dataTransfer.files);
  }

  function removeFile(index: number) {
    onChange(files.filter((_, i) => i !== index));
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{label}</p>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-6 text-center transition-colors ${
          dragOver ? "border-primary bg-secondary" : "border-border bg-card hover:bg-accent"
        }`}
      >
        <UploadIcon className="text-ink-400 size-6" />
        <p className="text-sm">
          Seret file ke sini, atau <span className="text-primary underline">pilih file</span>
        </p>
        <p className="caption">{hint}</p>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      {files.length > 0 && (
        <ul className="space-y-1">
          {files.map((file, i) => (
            <li
              key={`${file.name}-${i}`}
              className="border-border bg-card flex items-center justify-between rounded-md border px-3 py-2 text-sm"
            >
              <span className="flex items-center gap-2 truncate">
                <FileIcon className="text-ink-400 size-4 shrink-0" />
                <span className="truncate">{file.name}</span>
                <span className="caption shrink-0">{(file.size / 1024).toFixed(0)} KB</span>
              </span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(i);
                }}
                className="text-ink-400 hover:text-danger-700 shrink-0"
                aria-label={`Hapus ${file.name}`}
              >
                <XIcon className="size-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
