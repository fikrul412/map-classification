"use client";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./select";

interface DatePickerProps {
  value: number | undefined;
  onChange: (year: number) => void;
}

export function DatePicker({ value, onChange }: DatePickerProps) {
  const years = Array.from({ length: 9 }, (_, i) => 2017 + i); // 2017 - 2025

  return (
    <Select value={value?.toString()} onValueChange={(val) => onChange(Number(val))}>
      <SelectTrigger>
        <SelectValue placeholder="Select year" />
      </SelectTrigger>
      <SelectContent>
        {years.map((y) => (
          <SelectItem key={y} value={y.toString()}>
            {y}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
