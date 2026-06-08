import { useState } from "react";

type ImageCardProps = {
  path: string;
  apiUrl: string;
};

export default function ImageCard({ path, apiUrl }: ImageCardProps) {
  const [failed, setFailed] = useState(false);
  const src = `${apiUrl}/images/${path}`;

  if (failed) {
    return (
      <div className="image-card image-card--error">
        <span className="image-card__label">Image</span>
        <p className="image-card__path">{path}</p>
        <p className="image-card__error">Failed to load image</p>
      </div>
    );
  }

  return (
    <div className="image-card">
      <span className="image-card__label">Generated image</span>
      <img
        className="image-card__img"
        src={src}
        alt={`Generated: ${path}`}
        onError={() => setFailed(true)}
      />
      <p className="image-card__path">{path}</p>
    </div>
  );
}
