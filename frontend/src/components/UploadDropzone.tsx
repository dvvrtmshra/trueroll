import { useRef, useState } from "react";

interface UploadDropzoneProps {
  onFile: (file: File) => void;
  accept?: string;
  label?: string;
}

export default function UploadDropzone({ onFile, accept = ".csv,.xlsx", label = "Drop a CSV or XLSX file here" }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  function handleFile(file: File) {
    setFileName(file.name);
    onFile(file);
  }

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
        dragging ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-blue-400"
      }`}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
      />
      {fileName ? (
        <div>
          <p className="text-green-700 font-medium">{fileName}</p>
          <p className="text-xs text-gray-500 mt-1">Click to change</p>
        </div>
      ) : (
        <div>
          <p className="text-gray-600">{label}</p>
          <p className="text-xs text-gray-400 mt-1">or click to browse · Max 50 MB</p>
          <p className="text-xs text-gray-400">{accept}</p>
        </div>
      )}
    </div>
  );
}
