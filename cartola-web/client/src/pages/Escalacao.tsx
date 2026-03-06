import { trpc } from "@/lib/trpc";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Loader2 } from "lucide-react";
import { useState, useMemo, useCallback } from "react";
import { useLocation } from "wouter";
import { toast } from "sonner";
import { ClubeBadge } from "@/components/ClubeBadge";

const CAMISA_URL = "https://d2xsxph8kpxj0f.cloudfront.net/310419663031516744/oTZR9ZkHbDCNQCXXcPwoHW/camisa_derve_bc758971.png";

const POSICOES: Record<number, string> = { 1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC" };
const FORMACOES_LISTA = ["Automático (Recomendada)", "3-4-3", "3-5-2", "4-3-3", "4-4-2", "4-5-1", "5-3-2", "5-4-1"];

const POS_BADGE_COLORS: Record<string, string> = {
  GOL: "#EAB308", LAT: "#22C55E", ZAG: "#3B82F6", MEI: "#A855F7", ATA: "#EF4444", TEC: "#6B7280",
};

export default function Escalacao() {
  const [, setLocation] = useLocation();
  const [formacao, setFormacao] = useState("Automático (Recomendada)");
  const [orcamento, setOrcamento] = useState(100);

  const { data: mercadoStatus } = trpc.cartola.mercadoStatus.useQuery();
  const { data: orcDinamicoData } = trpc.estrategia.orcamentoDinamico.useQuery();
  const [orcInited, setOrcInited] = useState(false);

  const escalarMutation = trpc.estrategia.escalarTime.useMutation({
    onSuccess: () => toast.success("Time escalado com sucesso!"),
    onError: (err) => toast.error(`Erro: ${err.message}`),
  });
  const salvarMutation = trpc.estrategia.salvarEscalacao.useMutation({
    onSuccess: (data: any) => {
      if (data.sucesso) toast.success(data.mensagem);
      else toast.error(data.erro);
    },
    onError: (err) => toast.error(`Erro: ${err.message}`),
  });

  const escalacao = escalarMutation.data;

  // Set initial orcamento from server-calculated dynamic budget
  useMemo(() => {
    if (!orcInited && orcDinamicoData && orcDinamicoData.orcamento > 0) {
      setOrcamento(orcDinamicoData.orcamento);
      setOrcInited(true);
    }
  }, [orcDinamicoData, orcInited]);

  const handleEscalar = useCallback(() => {
    const f = formacao.startsWith("Automático") ? "auto" : formacao;
    escalarMutation.mutate({
      formacao: f,
      orcamento,
      rodada: mercadoStatus?.rodada_atual,
      ano: mercadoStatus?.temporada,
    });
  }, [formacao, orcamento, mercadoStatus]);

  const handleSalvar = useCallback(() => {
    if (!escalacao) return;
    salvarMutation.mutate({
      rodada: mercadoStatus?.rodada_atual || 0,
      ano: mercadoStatus?.temporada || 2026,
      formacao: escalacao.formacao,
      escalacao,
    });
  }, [escalacao, mercadoStatus]);

  // Group titulares by position for field layout
  // IMPORTANT: Defense line = LAT(left) + ZAG(center) + LAT(right) - matching Streamlit
  const linhas = useMemo(() => {
    if (!escalacao) return { gol: [], defesa: [], mei: [], ata: [], tec: [] };
    const group = (posIds: number[]) => escalacao.titulares.filter((j: any) => posIds.includes(j.pos_id));
    const lat = group([2]);
    const zag = group([3]);
    // Combine defense: LAT[0] + all ZAG + LAT[1] (laterais nas pontas, zagueiros no centro)
    let defesa: any[] = [];
    if (lat.length >= 2) {
      defesa = [lat[0], ...zag, lat[1]];
    } else if (lat.length === 1) {
      defesa = [lat[0], ...zag];
    } else {
      defesa = zag;
    }
    return {
      ata: group([5]),
      mei: group([4]),
      defesa,
      gol: group([1]),
      tec: group([6]),
    };
  }, [escalacao]);

  // Ordered list for side panel (GOL, LAT, ZAG, MEI, ATA, TEC)
  const titularesOrdenados = useMemo(() => {
    if (!escalacao) return [];
    const ordered: any[] = [];
    for (const posId of [1, 2, 3, 4, 5, 6]) {
      ordered.push(...escalacao.titulares.filter((j: any) => j.pos_id === posId));
    }
    return ordered;
  }, [escalacao]);

  const rodadaAtual = mercadoStatus?.rodada_atual || 0;
  const estrategiaLabel = rodadaAtual === 1 ? "Estratégia R1: Valorização Fácil" : "Estratégia: Modelo Preditivo";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold" style={{ color: "#f1f5f9", fontFamily: "var(--font-heading)" }}>
          Escalação Automática
        </h1>
        <p className="text-sm mt-1" style={{ color: "#94a3b8" }}>
          Rodada {rodadaAtual} | {mercadoStatus?.status_mercado === 1 ? "Mercado Aberto" : "Mercado Fechado"}
          {mercadoStatus?.fechamento?.timestamp && (
            <span> | Fechamento: {new Date(mercadoStatus.fechamento.timestamp * 1000).toLocaleString("pt-BR")}</span>
          )}
        </p>
      </div>

      {/* Controls */}
      <div className="rounded-xl p-5" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium" style={{ color: "#f1f5f9" }}>💰 Orçamento (C$)</label>
            <Input
              type="number" value={orcamento} onChange={(e) => setOrcamento(Number(e.target.value))}
              min={50} max={500} step={0.5}
              style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }}
            />
            <p className="text-xs" style={{ color: "#64748b" }}>Calculado pela valorização acumulada</p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium" style={{ color: "#f1f5f9" }}>📋 Formação</label>
            <Select value={formacao} onValueChange={setFormacao}>
              <SelectTrigger style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {FORMACOES_LISTA.map((f) => (
                  <SelectItem key={f} value={f}>{f}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-end">
            <Button onClick={handleEscalar} disabled={escalarMutation.isPending} className="w-full h-10"
              style={{ background: "#54b4f7", color: "#000", fontWeight: 700 }}>
              {escalarMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              ⚡ Escalar Time
            </Button>
          </div>
          <div className="flex items-end">
            <Button onClick={handleSalvar} disabled={!escalacao || salvarMutation.isPending} variant="outline" className="w-full h-10"
              style={{ borderColor: "rgba(52, 211, 153, 0.3)", color: "#34d399" }}>
              💾 Confirmar e Salvar
            </Button>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2">
          <span className="text-xs px-3 py-1 rounded-full" style={{ background: "rgba(84, 180, 247, 0.15)", color: "#54b4f7", border: "1px solid rgba(84, 180, 247, 0.3)" }}>
            {estrategiaLabel}
          </span>
        </div>
      </div>

      {/* Loading */}
      {escalarMutation.isPending && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin" style={{ color: "#54b4f7" }} />
          <span className="ml-3" style={{ color: "#94a3b8" }}>Calculando melhor escalação...</span>
        </div>
      )}

      {/* Escalação Result */}
      {escalacao && (
        <>
          {/* Field Header */}
          <div className="rounded-t-xl flex items-center justify-between flex-wrap gap-3 px-4 py-3"
            style={{ background: "linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9))", border: "1px solid rgba(148, 163, 184, 0.15)", borderBottom: "none" }}>
            <span className="font-extrabold text-lg tracking-wide" style={{ color: "#f1f5f9", fontFamily: "var(--font-heading)" }}>ESCALAÇÃO</span>
            <div className="flex items-center gap-4 flex-wrap">
              <span className="px-3 py-1 rounded-full text-sm font-bold" style={{ background: "rgba(77, 168, 240, 0.15)", color: "#4da8f0", border: "1px solid rgba(77, 168, 240, 0.3)" }}>
                {escalacao.formacao}
              </span>
              <div className="text-center">
                <span className="text-xs block" style={{ color: "#94a3b8" }}>PREVISTO</span>
                <span className="font-extrabold text-lg" style={{ color: "#34d399" }}>{escalacao.pontuacao_esperada?.toFixed(1)}</span>
              </div>
              <div className="text-right">
                <span className="text-xs block" style={{ color: "#94a3b8" }}>MEU TIME</span>
                <span className="font-bold text-sm" style={{ color: "#4da8f0" }}>C$ {escalacao.custo_total?.toFixed(2)}</span>
              </div>
              <div className="text-right">
                <span className="text-xs block" style={{ color: "#94a3b8" }}>SALDO</span>
                <span className="font-bold text-sm" style={{ color: "#f1f5f9" }}>C$ {escalacao.orcamento_restante?.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Football Field + Side List */}
          <div className="flex gap-0" style={{ minHeight: 580 }}>
            {/* Field */}
            <div className="flex-[3] relative rounded-bl-xl overflow-hidden" style={{
              background: "linear-gradient(180deg, #1a6b30 0%, #15802d 15%, #1a6b30 30%, #15802d 45%, #1a6b30 60%, #15802d 75%, #1a6b30 90%, #15802d 100%)",
              border: "1px solid rgba(148, 163, 184, 0.15)", borderTop: "2px solid rgba(255,255,255,0.2)", borderRight: "none",
            }}>
              {/* Field lines */}
              <div className="absolute" style={{ top: 0, left: "5%", right: "5%", bottom: 0, border: "2px solid rgba(255,255,255,0.2)", borderTop: "none" }} />
              <div className="absolute" style={{ top: "50%", left: "5%", right: "5%", height: 2, background: "rgba(255,255,255,0.15)" }} />
              <div className="absolute" style={{ top: "50%", left: "50%", width: 70, height: 70, border: "2px solid rgba(255,255,255,0.15)", borderRadius: "50%", transform: "translate(-50%, -50%)" }} />
              <div className="absolute" style={{ top: 0, left: "25%", right: "25%", height: 55, border: "2px solid rgba(255,255,255,0.15)", borderTop: "none" }} />
              <div className="absolute" style={{ bottom: 0, left: "25%", right: "25%", height: 55, border: "2px solid rgba(255,255,255,0.15)", borderBottom: "none" }} />

              {/* Players */}
              <div className="relative z-10 flex flex-col justify-between py-4 gap-2" style={{ minHeight: 540 }}>
                <FieldRow jogadores={linhas.ata} capitaoId={escalacao.capitao?.atleta_id} onClickJogador={(id) => setLocation(`/jogador/${id}`)} />
                <FieldRow jogadores={linhas.mei} capitaoId={escalacao.capitao?.atleta_id} onClickJogador={(id) => setLocation(`/jogador/${id}`)} />
                {/* Defense: LAT(left) + ZAG(center) + LAT(right) */}
                <FieldRow jogadores={linhas.defesa} capitaoId={escalacao.capitao?.atleta_id} onClickJogador={(id) => setLocation(`/jogador/${id}`)} />
                {/* Goleiro + Técnico */}
                <div className="flex justify-center items-start px-5 relative">
                  <div className="flex-1" />
                  <div className="flex-shrink-0">
                    {linhas.gol.map((j: any) => (
                      <FieldPlayer key={j.atleta_id} jogador={j} isCap={escalacao.capitao?.atleta_id === j.atleta_id} onClick={() => setLocation(`/jogador/${j.atleta_id}`)} />
                    ))}
                  </div>
                  <div className="flex-1 flex justify-end pr-2">
                    {linhas.tec.map((j: any) => (
                      <FieldPlayer key={j.atleta_id} jogador={j} isCap={false} isTec onClick={() => setLocation(`/jogador/${j.atleta_id}`)} />
                    ))}
                  </div>
                </div>
              </div>

              {/* Formation watermark */}
              <div className="absolute bottom-4 left-4 z-20">
                <span style={{ color: "rgba(255,255,255,0.35)", fontSize: "1.6rem", fontWeight: 800, fontFamily: "var(--font-heading)", letterSpacing: 1 }}>
                  {escalacao.formacao}
                </span>
              </div>
            </div>

            {/* Side List - matching Streamlit campo_layout.py gerar_lista_lateral_markdown */}
            <div className="flex-[2] rounded-br-xl overflow-y-auto" style={{
              background: "linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.6) 100%)",
              border: "1px solid rgba(148, 163, 184, 0.15)", borderLeft: "none", borderTop: "2px solid rgba(148, 163, 184, 0.15)",
              padding: "8px 12px",
            }}>
              {/* Header */}
              <div className="flex justify-between items-center pb-2 mb-1" style={{ borderBottom: "2px solid rgba(148, 163, 184, 0.2)" }}>
                <div className="flex items-center gap-2">
                  <span className="text-[0.65rem] font-bold tracking-wider" style={{ color: "#64748b", minWidth: 28 }}>POS</span>
                  <span className="text-[0.65rem] font-bold tracking-wider" style={{ color: "#64748b" }}>JOGADOR</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[0.65rem] font-bold tracking-wider" style={{ color: "#4da8f0", minWidth: 60, textAlign: "right" }}>PREÇO</span>
                  <span className="text-[0.65rem] font-bold tracking-wider" style={{ color: "#34d399", minWidth: 42, textAlign: "right" }}>PTS</span>
                </div>
              </div>

              {/* Titulares */}
              {titularesOrdenados.map((j: any) => {
                const isCap = escalacao.capitao?.atleta_id === j.atleta_id;
                const pos = POSICOES[j.pos_id] || "?";
                return (
                  <button key={j.atleta_id} onClick={() => setLocation(`/jogador/${j.atleta_id}`)}
                    className="w-full flex justify-between items-center py-1.5 hover:opacity-80"
                    style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}>
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-[0.7rem] font-semibold" style={{ color: "#64748b", minWidth: 28 }}>{pos}</span>
                      {isCap && (
                        <span className="inline-flex items-center justify-center rounded-full shrink-0"
                          style={{ width: 16, height: 16, background: "#FFD700", color: "#000", fontSize: "0.55rem", fontWeight: 800 }}>C</span>
                      )}
                      <span className="text-[0.8rem] font-bold truncate" style={{ color: "#f1f5f9" }}>{j.apelido?.toUpperCase()}</span>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-[0.75rem] font-semibold" style={{ color: "#4da8f0", minWidth: 60, textAlign: "right" }}>C$ {j.preco?.toFixed(2)}</span>
                      <span className="text-[0.8rem] font-bold" style={{ color: "#34d399", minWidth: 42, textAlign: "right" }}>{j.pontuacao_esperada?.toFixed(1)}</span>
                    </div>
                  </button>
                );
              })}

              {/* Banco de Reservas separator */}
              <div className="flex items-center justify-center my-3 gap-2">
                <div className="flex-1 h-px" style={{ background: "rgba(148, 163, 184, 0.2)" }} />
                <span className="text-[0.65rem] font-bold tracking-widest whitespace-nowrap" style={{ color: "#94a3b8" }}>BANCO DE RESERVAS</span>
                <div className="flex-1 h-px" style={{ background: "rgba(148, 163, 184, 0.2)" }} />
              </div>

              {/* Reservas */}
              {escalacao.reservas && Object.entries(escalacao.reservas).map(([posId, reserva]) => {
                if (!reserva) return null;
                const r = reserva as any;
                const isLuxo = escalacao.reserva_luxo?.atleta_id === r.atleta_id;
                const pos = POSICOES[Number(posId)] || posId;
                return (
                  <button key={posId} onClick={() => setLocation(`/jogador/${r.atleta_id}`)}
                    className="w-full flex justify-between items-center py-1.5 hover:opacity-80"
                    style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}>
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-[0.7rem] font-semibold" style={{ color: "#64748b", minWidth: 28 }}>{pos}</span>
                      {isLuxo && <span className="text-[0.55rem] mr-0.5">⭐</span>}
                      <span className="text-[0.8rem] font-bold truncate" style={{ color: "#cbd5e1" }}>{r.apelido?.toUpperCase()}</span>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-[0.75rem] font-semibold" style={{ color: "#64748b", minWidth: 60, textAlign: "right" }}>C$ {r.preco?.toFixed(2)}</span>
                      <span className="text-[0.8rem] font-bold" style={{ color: "#64748b", minWidth: 42, textAlign: "right" }}>{r.pontuacao_esperada?.toFixed(1)}</span>
                    </div>
                  </button>
                );
              })}

              {/* Reserva de Luxo (if separate from reservas) */}
              {escalacao.reserva_luxo && !Object.values(escalacao.reservas || {}).some((r: any) => r?.atleta_id === escalacao.reserva_luxo?.atleta_id) && (
                <button onClick={() => setLocation(`/jogador/${escalacao.reserva_luxo!.atleta_id}`)}
                  className="w-full flex justify-between items-center py-1.5 hover:opacity-80"
                  style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}>
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-[0.7rem] font-semibold" style={{ color: "#64748b", minWidth: 28 }}>{POSICOES[escalacao.reserva_luxo.pos_id] || "?"}</span>
                    <span className="text-[0.55rem] mr-0.5">⭐</span>
                    <span className="text-[0.8rem] font-bold truncate" style={{ color: "#cbd5e1" }}>{escalacao.reserva_luxo.apelido?.toUpperCase()}</span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-[0.75rem] font-semibold" style={{ color: "#64748b", minWidth: 60, textAlign: "right" }}>C$ {escalacao.reserva_luxo.preco?.toFixed(2)}</span>
                    <span className="text-[0.8rem] font-bold" style={{ color: "#64748b", minWidth: 42, textAlign: "right" }}>{escalacao.reserva_luxo.pontuacao_esperada?.toFixed(1)}</span>
                  </div>
                </button>
              )}
            </div>
          </div>

          {/* Capitão + Vice */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Capitão */}
            {escalacao.capitao && (
              <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(255, 215, 0, 0.2)" }}>
                <h4 className="font-bold mb-3 flex items-center gap-2" style={{ color: "#FFD700" }}>👑 Capitão (x1.5)</h4>
                <button onClick={() => setLocation(`/jogador/${escalacao.capitao!.atleta_id}`)} className="w-full flex items-center justify-between p-2 rounded-lg hover:opacity-80">
                  <div className="flex items-center gap-3">
                    <ClubeBadge clubeId={escalacao.capitao.clube_id} size={24} />
                    <div className="text-left">
                      <p className="font-bold" style={{ color: "#f1f5f9" }}>{escalacao.capitao.apelido}</p>
                      <p className="text-xs" style={{ color: "#94a3b8" }}>{escalacao.capitao.posicao} | {escalacao.capitao.clube}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold" style={{ color: "#FFD700" }}>{(escalacao.capitao.pontuacao_esperada * 1.5).toFixed(1)} pts</p>
                    <p className="text-xs" style={{ color: "#94a3b8" }}>({escalacao.capitao.pontuacao_esperada.toFixed(1)} x 1.5)</p>
                  </div>
                </button>
              </div>
            )}
            {/* Vice-Capitão */}
            {escalacao.vice_capitao && (
              <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                <h4 className="font-bold mb-3 flex items-center gap-2" style={{ color: "#94a3b8" }}>👥 Vice-Capitão</h4>
                <button onClick={() => setLocation(`/jogador/${escalacao.vice_capitao!.atleta_id}`)} className="w-full flex items-center justify-between p-2 rounded-lg hover:opacity-80">
                  <div className="flex items-center gap-3">
                    <ClubeBadge clubeId={escalacao.vice_capitao.clube_id} size={24} />
                    <div className="text-left">
                      <p className="font-bold" style={{ color: "#f1f5f9" }}>{escalacao.vice_capitao.apelido}</p>
                      <p className="text-xs" style={{ color: "#94a3b8" }}>{escalacao.vice_capitao.posicao} | {escalacao.vice_capitao.clube}</p>
                    </div>
                  </div>
                  <p className="text-lg font-bold" style={{ color: "#cbd5e1" }}>{escalacao.vice_capitao.pontuacao_esperada?.toFixed(1)} pts</p>
                </button>
              </div>
            )}
          </div>

          {/* Titulares Detail Table - Streamlit style */}
          <div className="rounded-xl p-5" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
            <h3 className="text-lg font-bold mb-4" style={{ color: "#f1f5f9" }}>📋 Detalhes dos Titulares</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.15)" }}>
                    <th className="text-left py-2 px-2" style={{ color: "#94a3b8" }}>Jogador</th>
                    <th className="text-center py-2 px-2" style={{ color: "#94a3b8" }}>Pos</th>
                    <th className="text-left py-2 px-2" style={{ color: "#94a3b8" }}>Clube</th>
                    <th className="text-right py-2 px-2" style={{ color: "#94a3b8" }}>Preço</th>
                    <th className="text-right py-2 px-2" style={{ color: "#94a3b8" }}>Score</th>
                    <th className="text-right py-2 px-2" style={{ color: "#94a3b8" }}>Val. Prev.</th>
                    <th className="text-left py-2 px-2" style={{ color: "#94a3b8" }}>Justificativa</th>
                    <th className="text-center py-2 px-2" style={{ color: "#94a3b8" }}>Papel</th>
                  </tr>
                </thead>
                <tbody>
                  {escalacao.titulares.map((j: any) => {
                    const isCap = escalacao.capitao?.atleta_id === j.atleta_id;
                    const pos = j.posicao || POSICOES[j.pos_id] || "?";
                    return (
                      <tr key={j.atleta_id} className="cursor-pointer hover:opacity-80" onClick={() => setLocation(`/jogador/${j.atleta_id}`)}
                        style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}>
                        <td className="py-2 px-2">
                          <div className="flex items-center gap-2">
                            <ClubeBadge clubeId={j.clube_id || 0} size={16} showName={false} />
                            <span className="font-bold" style={{ color: "#f1f5f9" }}>{j.apelido}</span>
                          </div>
                        </td>
                        <td className="py-2 px-2 text-center">
                          <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: `${POS_BADGE_COLORS[pos]}20`, color: POS_BADGE_COLORS[pos] }}>
                            {pos}
                          </span>
                        </td>
                        <td className="py-2 px-2 text-xs" style={{ color: "#94a3b8" }}>{j.clube}</td>
                        <td className="py-2 px-2 text-right font-semibold" style={{ color: "#4da8f0" }}>C$ {j.preco?.toFixed(2)}</td>
                        <td className="py-2 px-2 text-right font-bold" style={{ color: "#34d399" }}>{j.pontuacao_esperada?.toFixed(1)}</td>
                        <td className="py-2 px-2 text-right" style={{ color: (j.valorizacao_prevista || 0) >= 0 ? "#34d399" : "#f87171" }}>
                          {(j.valorizacao_prevista || 0) >= 0 ? "+" : ""}{j.valorizacao_prevista?.toFixed(2) || "0.00"}
                        </td>
                        <td className="py-2 px-2 text-xs max-w-[200px] truncate" style={{ color: "#cbd5e1" }}>
                          {j.explicacao?.resumo || "—"}
                        </td>
                        <td className="py-2 px-2 text-center">
                          {isCap && <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: "rgba(255, 215, 0, 0.15)", color: "#FFD700" }}>CAP</span>}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Strategy info */}
          {escalacao.estrategia_especial && (
            <div className="rounded-xl p-4 flex items-start gap-3" style={{ background: "rgba(84, 180, 247, 0.08)", border: "1px solid rgba(84, 180, 247, 0.2)" }}>
              <span style={{ color: "#54b4f7" }}>💡</span>
              <div>
                <p className="text-sm font-bold" style={{ color: "#f1f5f9" }}>Estratégia Especial</p>
                <p className="text-sm" style={{ color: "#94a3b8" }}>{escalacao.estrategia_especial}</p>
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty state */}
      {!escalacao && !escalarMutation.isPending && (
        <div className="rounded-xl p-12 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
          <img src={CAMISA_URL} alt="" className="h-20 w-20 mx-auto mb-4 opacity-30" />
          <h3 className="text-lg font-bold mb-2" style={{ color: "#f1f5f9" }}>Nenhuma escalação ativa</h3>
          <p className="text-sm max-w-md mx-auto" style={{ color: "#94a3b8" }}>
            Selecione uma formação e orçamento, depois clique em "Escalar Time" para gerar a escalação otimizada.
          </p>
        </div>
      )}
    </div>
  );
}

function FieldRow({ jogadores, capitaoId, onClickJogador }: { jogadores: any[]; capitaoId?: string; onClickJogador: (id: string) => void }) {
  if (!jogadores || jogadores.length === 0) return null;
  return (
    <div className="flex justify-evenly items-start px-2">
      {jogadores.map((j: any) => (
        <FieldPlayer key={j.atleta_id} jogador={j} isCap={capitaoId === j.atleta_id} onClick={() => onClickJogador(j.atleta_id)} />
      ))}
    </div>
  );
}

function FieldPlayer({ jogador, isCap, isTec, onClick }: { jogador: any; isCap: boolean; isTec?: boolean; onClick: () => void }) {
  const apelido = jogador.apelido?.length > 11 ? jogador.apelido.substring(0, 10) + "." : jogador.apelido;
  return (
    <button onClick={onClick} className="flex flex-col items-center relative group" style={{ minWidth: 80 }}>
      {/* Captain badge */}
      {isCap && (
        <span className="absolute -top-1 -right-1 z-10 flex items-center justify-center rounded-full"
          style={{ width: 16, height: 16, background: "#FFD700", color: "#000", fontSize: "0.55rem", fontWeight: 800 }}>
          C
        </span>
      )}
      {/* Jersey */}
      <img src={CAMISA_URL} alt="" className="group-hover:scale-110 transition-transform"
        style={{ width: isTec ? 44 : 50, height: isTec ? 48 : 54, objectFit: "contain", filter: `drop-shadow(0 2px 4px rgba(0,0,0,0.5))${isTec ? " brightness(0.85)" : ""}` }} />
      {/* Label */}
      <div className="mt-0.5 text-center rounded px-2 py-0.5" style={{ background: "rgba(0,0,0,0.65)", minWidth: 70 }}>
        <div className="font-bold truncate" style={{ color: "#fff", fontSize: "0.65rem", maxWidth: 90 }}>{apelido}</div>
        <div className="font-semibold" style={{ color: "#4da8f0", fontSize: "0.6rem" }}>C$ {jogador.preco?.toFixed(2)}</div>
        <div className="font-bold" style={{ color: "#34d399", fontSize: "0.55rem" }}>{jogador.pontuacao_esperada?.toFixed(1)}p</div>
      </div>
    </button>
  );
}
