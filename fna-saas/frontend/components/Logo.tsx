"use client";

import { useState } from "react";

interface LogoProps {
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  variant?: "full" | "icon" | "wordmark";
  className?: string;
}

const sizes = {
  xs: { img: 24, textCls: "text-base" },
  sm: { img: 32, textCls: "text-lg" },
  md: { img: 44, textCls: "text-xl" },
  lg: { img: 64, textCls: "text-3xl" },
  xl: { img: 96, textCls: "text-4xl" },
};

function AdvoraFallback({ size }: { size: number }) {
  return (
    <div
      className="rounded-full flex items-center justify-center shrink-0"
      style={{
        width: size,
        height: size,
        background: "linear-gradient(135deg, #7c3aed 0%, #06b6d4 50%, #f97316 100%)",
      }}
    >
      <span
        className="font-black text-white"
        style={{ fontSize: Math.round(size * 0.45) }}
      >
        A
      </span>
    </div>
  );
}

export function Logo({ size = "md", variant = "full", className = "" }: LogoProps) {
  const [imgError, setImgError] = useState(false);
  const s = sizes[size];

  if (variant === "wordmark") {
    return (
      <span className={`font-bold tracking-tight text-navy-800 ${s.textCls} ${className}`}>
        Advora
      </span>
    );
  }

  const icon = imgError ? (
    <AdvoraFallback size={s.img} />
  ) : (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/logo.png"
      alt="Advora logo"
      width={s.img}
      height={s.img}
      className="object-contain shrink-0"
      style={{ width: s.img, height: s.img }}
      onError={() => setImgError(true)}
    />
  );

  if (variant === "icon") return <>{icon}</>;

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      {icon}
      <div className="flex flex-col leading-none">
        <span className={`font-bold tracking-tight text-navy-800 ${s.textCls}`}>
          Advora
        </span>
        {size !== "xs" && size !== "sm" && (
          <span className="text-[10px] font-semibold tracking-[0.2em] uppercase text-advora-sky mt-0.5">
            Your Voice
          </span>
        )}
      </div>
    </div>
  );
}
