"use client";

import { useRef, useState } from "react";
import { Upload, X, Loader2, Image as ImageIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { api, getToken } from "@/lib/api";
import { toast } from "sonner";

interface ImageUploadProps {
  currentUrl?: string | null;
  uploadUrl: string;          // e.g. /uploads/business/{id}/logo
  onUploaded: (url: string) => void;
  label?: string;
  hint?: string;
  shape?: "square" | "circle";
  aspectRatio?: "1:1" | "16:9" | "4:3";
  className?: string;
  maxSizeMB?: number;
}

const ASPECT_PADDING: Record<string, string> = {
  "1:1":  "pb-[100%]",
  "16:9": "pb-[56.25%]",
  "4:3":  "pb-[75%]",
};

export function ImageUpload({
  currentUrl,
  uploadUrl,
  onUploaded,
  label = "Upload image",
  hint = "PNG, JPG or WebP up to 10 MB",
  shape = "square",
  aspectRatio = "1:1",
  className,
  maxSizeMB = 10,
}: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(currentUrl ?? null);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);

  const handleFile = async (file: File) => {
    // Client-side validation
    if (!file.type.startsWith("image/")) {
      toast.error("Please select an image file (PNG, JPG, WebP, GIF)");
      return;
    }
    if (file.size > maxSizeMB * 1024 * 1024) {
      toast.error(`File size must be under ${maxSizeMB} MB`);
      return;
    }

    // Show local preview immediately
    const objectUrl = URL.createObjectURL(file);
    setPreview(objectUrl);
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
      const token = getToken();

      const res = await fetch(`${BASE}${uploadUrl}`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });

      if (!res.ok) {
        let msg = "Upload failed";
        try {
          const err = await res.json();
          msg = err?.detail ?? msg;
        } catch { /* ignore */ }
        throw new Error(msg);
      }

      const data = await res.json();
      onUploaded(data.url);
      setPreview(data.url);
      toast.success("Image uploaded successfully");
    } catch (err: any) {
      toast.error(err.message ?? "Upload failed");
      setPreview(currentUrl ?? null);
    } finally {
      setUploading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const clearImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    setPreview(null);
    onUploaded("");
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className={cn("space-y-1.5", className)}>
      {label && <p className="text-sm font-medium text-gray-700">{label}</p>}

      <div
        className={cn(
          "relative border-2 border-dashed transition-colors cursor-pointer overflow-hidden",
          shape === "circle" ? "rounded-full" : "rounded-xl",
          dragging
            ? "border-brand-400 bg-brand-50"
            : preview
            ? "border-gray-200"
            : "border-gray-300 hover:border-brand-400 hover:bg-brand-50/30",
          "group"
        )}
        onClick={() => !uploading && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        {/* Aspect ratio box */}
        <div className={cn("relative w-full", ASPECT_PADDING[aspectRatio])}>
          <div className="absolute inset-0">
            {preview ? (
              <>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={preview}
                  alt="Preview"
                  className="w-full h-full object-cover"
                />
                {/* Overlay on hover */}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
                  <div className="bg-white/90 rounded-full p-2">
                    <Upload className="w-4 h-4 text-gray-700" />
                  </div>
                  <button
                    type="button"
                    onClick={clearImage}
                    className="bg-white/90 rounded-full p-2 hover:bg-red-100"
                    aria-label="Remove image"
                  >
                    <X className="w-4 h-4 text-red-600" />
                  </button>
                </div>
                {/* Upload progress */}
                {uploading && (
                  <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                    <div className="bg-white rounded-xl px-4 py-2 flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
                      <span className="text-sm font-medium text-gray-700">Uploading…</span>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center p-4 text-center">
                {uploading ? (
                  <Loader2 className="w-8 h-8 animate-spin text-brand-600 mb-2" />
                ) : (
                  <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mb-3 group-hover:bg-brand-50 transition-colors">
                    <Upload className="w-5 h-5 text-gray-400 group-hover:text-brand-600 transition-colors" />
                  </div>
                )}
                {!uploading && (
                  <>
                    <p className="text-sm font-medium text-gray-700 group-hover:text-brand-700">
                      Click or drag to upload
                    </p>
                    {hint && (
                      <p className="text-xs text-gray-400 mt-1">{hint}</p>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif"
        className="sr-only"
        onChange={handleInputChange}
        aria-label={label}
      />
    </div>
  );
}
