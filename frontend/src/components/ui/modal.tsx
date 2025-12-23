"use client";
import { useState } from "react";
import { Button } from "./button";

interface ModalProps {
  onClose: () => void;
  onSave: (clientId: string, clientPassword: string) => void;
}

export function Modal({ onClose, onSave }: ModalProps) {
  const [id, setId] = useState("");
  const [password, setPassword] = useState("");

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96 shadow-lg flex flex-col gap-4">
        <h2 className="text-lg font-bold">Set Client Credentials</h2>
        <input
          type="text"
          placeholder="Client ID"
          value={id}
          onChange={(e) => setId(e.target.value)}
          className="border p-2 rounded w-full"
        />
        <input
          type="password"
          placeholder="Client Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="border p-2 rounded w-full"
        />
        <div className="flex justify-end gap-2 mt-2">
          <Button onClick={onClose} variant="outline">Cancel</Button>
          <Button onClick={() => onSave(id, password)}>Save</Button>
        </div>
      </div>
    </div>
  );
}
