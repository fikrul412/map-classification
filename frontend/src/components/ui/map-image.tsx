interface MapImageProps {
  src: string;
}

export function MapImage({ src }: MapImageProps) {
  return (
    <img
      src={src || "https://via.placeholder.com/512"} // fallback placeholder
      alt="Map Prediction"
      className="h-full w-full object-cover dark:brightness-[0.2] dark:grayscale bg-muted rounded-lg"
    />
  );
}
