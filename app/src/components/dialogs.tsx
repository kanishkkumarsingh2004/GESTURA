"use client";

import { HTMLAttributes, useCallback } from "react";
import { Trash2, RotateCcw } from "lucide-react";

interface ConfirmDialogProps extends HTMLAttributes<HTMLDivElement> {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  danger?: boolean;
}

export function ConfirmDialog({
  open,
  onClose,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  onConfirm,
  danger = false,
}: ConfirmDialogProps) {
  const handleKey = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose]
  );

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      onKeyDown={handleKey}
    >
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="bg-slate border border-slate-700 rounded-xl p-6 shadow-xl w-full max-w-sm">
        <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
        {description && (
          <p className="text-slate-400 text-sm mb-6">{description}</p>
        )}
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-md text-sm font-medium text-slate-300 hover:bg-slate-800"
          >
            {cancelLabel}
          </button>
          <button
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              danger
                ? "text-red-400 bg-red-900/20 hover:bg-red-500/30 border border-red-500/30"
                : "text-white bg-electric-blue hover:bg-cyan-400"
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export function DeleteButton({
  onDelete,
  label = "Delete",
}: {
  onDelete: () => void;
  label?: string;
}) {
  const [open, setOpen] = React.useState(false);
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="text-red-400 hover:text-red-300 text-sm"
      >
        <Trash2 className="w-4 h-4" /> {label}
      </button>
      <ConfirmDialog
        open={open}
        onClose={() => setOpen(false)}
        title="Delete?"
        description="This action cannot be undone."
        confirmLabel="Delete"
        cancelLabel="Cancel"
        onConfirm={onDelete}
        danger
      />
    </>
  );
}

import React from "react";

export function RefreshButton({
  onRefresh,
  label = "Refresh",
}: {
  onRefresh: () => void;
  label?: string;
}) {
  return (
    <button
      onClick={onRefresh}
      className="flex items-center gap-1 text-electric-blue hover:text-cyan-400 text-sm font-medium"
    >
      <RotateCcw className="w-4 h-4" /> {label}
    </button>
  );
}
