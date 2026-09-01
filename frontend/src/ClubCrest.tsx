import React, { useMemo } from 'react';

type ClubCrestProps = {
  crestUrl: string | null;
  name: string;
};

export default function ClubCrest({ crestUrl, name }: ClubCrestProps) {
  const slot = useMemo(() => {
    const match = crestUrl?.match(/#slot=(\d+)$/);
    return match ? Number(match[1]) : null;
  }, [crestUrl]);

  if (slot === null) {
    return <span className="club-crest club-crest-missing" aria-label={`${name} crest unavailable`} />;
  }

  const col = slot % 13;
  const row = Math.floor(slot / 13);

  return (
    <span
      className="club-crest"
      role="img"
      aria-label={`${name} crest`}
      style={{
        backgroundImage: "url('/club-logos-sprite.webp')",
        backgroundSize: '286px 286px',
        backgroundPosition: `${-col * 22}px ${-row * 22}px`,
      }}
    />
  );
}
