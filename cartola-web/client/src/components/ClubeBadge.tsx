import { useClubes } from "@/hooks/useClubes";

export function ClubeBadge({
  clubeId,
  clubeNome,
  size = 20,
  showName = true,
  className = "",
}: {
  clubeId?: number | string;
  clubeNome?: string;
  size?: number;
  showName?: boolean;
  className?: string;
}) {
  const { getEscudo, getNome } = useClubes();
  const escudo = getEscudo(clubeId, size > 35 ? "45" : "30");
  const nome = clubeNome || getNome(clubeId);

  return (
    <span className={`inline-flex items-center gap-1.5 ${className}`}>
      {escudo ? (
        <img
          src={escudo}
          alt={nome}
          width={size}
          height={size}
          className="inline-block"
          style={{ width: size, height: size }}
          loading="lazy"
        />
      ) : null}
      {showName && <span className="text-muted-foreground text-sm">{nome}</span>}
    </span>
  );
}
