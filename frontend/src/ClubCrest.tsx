import React, { useState } from 'react';

type ClubCrestProps = {
  crestUrl: string | null;
  name: string;
};

export default function ClubCrest({ crestUrl, name }: ClubCrestProps) {
  const [imageFailed, setImageFailed] = useState(false);
  const directImageUrl = crestUrl && !crestUrl.includes('#slot=') ? crestUrl : null;

  if (!directImageUrl || imageFailed) {
    return (
      <span
        className="club-crest club-crest-missing"
        role="img"
        aria-label={`${name} crest unavailable`}
      />
    );
  }

  return (
    <img
      className="club-crest"
      src={directImageUrl}
      alt={`${name} crest`}
      loading="lazy"
      decoding="async"
      onError={() => setImageFailed(true)}
      style={{ objectFit: 'contain', display: 'block' }}
    />
  );
}
