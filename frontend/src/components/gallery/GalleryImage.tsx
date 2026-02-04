import type { ImgHTMLAttributes } from "react";

interface GalleryImageProps extends ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  className?: string;
}

export function GalleryImage({
  src,
  className = "",
  alt = "",
  ...props
}: GalleryImageProps) {
  return <img src={src} alt={alt} className={`gallery-image ${className}`} {...props} />;
}