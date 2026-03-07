import { trpc } from "@/lib/trpc";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Loader2, ChevronDown, ChevronUp, ArrowRightLeft, X, Trophy } from "lucide-react";
import { useState, useMemo, useCallback, useEffect } from "react";
import { useLocation } from "wouter";
import { toast } from "sonner";
import { ClubeBadge } from "@/components/ClubeBadge";

const CAMISA_URL = "https://d2xsxph8kpxj0f.cloudfront.net/310419663031516744/oTZR9ZkHbDCNQCXXcPwoHW/camisa_derve_bc758971.png";

const POSICOES: Record<number, string> = { 1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC" };
const FORMACOES_LISTA = ["Automático (Recomendada)", "3-4-3", "3-5-2", "4-3-3", "4-4-2", "4-5-1", "5-3-2", "5-4-1"];

const POS_BADGE_COLORS: Record<string, string> = {
  GOL: "#EAB308", LAT: "#22C55E", ZAG: "#3B82F6", MEI: "#A855F7", ATA: "#EF4444", TEC: "#6B7280",
};

const STORAGE_KEY = "cartola_escalacao_v1";

// Persist escalacao to localStorage
function saveToStorage(data: any) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {}
}

function loadFromStorage(): any | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return null;
}

function clearStorage() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {}
}

export default function Escalacao() {
  const [, setLocation] = useLocation();
  const [formacao, setFormacao] = useState("Automático (Recomendada)");
  const [orcamento, setOrcamento] = useState(100);
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());
  const [substituindo, setSubstituindo] = useState<string | null>(null);
  const [excluirIds, setExcluirIds] = useState<string[]>([]);
  const [activeTop10Tab, setActiveTop10Tab] = useState(1);

  const { data: mercadoStatus } = trpc.cartola.mercadoStatus.useQuery();
  const { data: orcDinamicoData } = trpc.estrategia.orcamentoDinamico.useQuery();
  const { data: mercadoData } = trpc.cartola.atletasMercado.useQuery();
  const [orcInited, setOrcInited] = useState(false);

  const escalarMutation = trpc.estrategia.escalarTime.useMutation({
    onSuccess: () => toast.success("Time escalado com sucesso!"),
    onError: (err: any) => toast.error(`Erro: ${err.message}`),
  });
  const salvarMutation = trpc.estrategia.salvarEscalacao.useMutation({
    onSuccess: (data: any) => {
      if (data.sucesso) toast.success(data.mensagem);
      else toast.error(data.erro);
    },
    onError: (err: any) => toast.error(`Erro: ${err.message}`),
  });

  const [escalacaoLocal, setEscalacaoLocal] = useState<any>(null);
  
  // Load persisted escalacao on mount
  useEffect(() => {
    const saved = loadFromStorage();
    if (saved && !escalacaoLocal && !escalarMutation.data) {
      setEscalacaoLocal(saved);
    }
  }, []);

  const escalacao = escalacaoLocal || escalarMutation.data;

  // Set initial orcamento from server-calculated dynamic budget
  useMemo(() => {
    if (!orcInited && orcDinamicoData && orcDinamicoData.orcamento > 0) {
      setOrcamento(orcDinamicoData.orcamento);
      setOrcInited(true);
    }
  }, [orcDinamicoData, orcInited]);

  // When mutation succeeds, copy to local state and persist
  useEffect(() => {
    if (escalarMutation.data && !escalacaoLocal) {
      const copy = JSON.parse(JSON.stringify(escalarMutation.data));
      setEscalacaoLocal(copy);
      saveToStorage(copy);
    }
  }, [escalarMutation.data]);

  // Persist whenever escalacaoLocal changes
  useEffect(() => {
    if (escalacaoLocal) {
      saveToStorage(escalacaoLocal);
    }
  }, [escalacaoLocal]);

  const handleEscalar = useCallback(() => {
    setEscalacaoLocal(null);
    clearStorage();
    setExpandedCards(new Set());
    setSubstituindo(null);
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

  // Re-escalar excluding a player (substituição = re-escalação sem o jogador)
  const handleSubstituir = useCallback((atletaIdSaiu: string) => {
    if (!escalacao) return;
    const jogadorSaindo = escalacao.titulares.find((t: any) => String(t.atleta_id) === atletaIdSaiu);
    if (!jogadorSaindo) return;
    
    const newExcluir = [...excluirIds, atletaIdSaiu];
    setExcluirIds(newExcluir);
    setEscalacaoLocal(null);
    clearStorage();
    setExpandedCards(new Set());
    setSubstituindo(null);
    
    const f = formacao.startsWith("Automático") ? "auto" : formacao;
    toast.info(`Removendo ${jogadorSaindo.apelido} e re-escalando...`);
    escalarMutation.mutate({
      formacao: f,
      orcamento,
      rodada: mercadoStatus?.rodada_atual,
      ano: mercadoStatus?.temporada,
      excluirIds: newExcluir,
    });
  }, [escalacao, excluirIds, formacao, orcamento, mercadoStatus]);

  // Cancel substitution mode
  const handleCancelSubstituicao = useCallback(() => {
    setSubstituindo(null);
  }, []);

  // Reset excluded players
  const handleResetExcluidos = useCallback(() => {
    setExcluirIds([]);
  }, []);


  const toggleCard = (id: string) => {
    setExpandedCards(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  // Group titulares by position for field layout
  const linhas = useMemo(() => {
    if (!escalacao) return { gol: [], defesa: [], mei: [], ata: [], tec: [] };
    const group = (posIds: number[]) => escalacao.titulares.filter((j: any) => posIds.includes(j.pos_id));
    const lat = group([2]);
    const zag = group([3]);
    let defesa: any[] = [];
    if (lat.length >= 2) {
      defesa = [lat[0], ...zag, lat[1]];
    } else if (lat.length === 1) {
      defesa = [lat[0], ...zag];
    } else {
      defesa = zag;
    }
    return { ata: group([5]), mei: group([4]), defesa, gol: group([1]), tec: group([6]) };
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
  const mercadoFechado = mercadoStatus?.status_mercado === 2;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold" style={{ color: "#f1f5f9", fontFamily: "var(--font-heading)" }}>
          Escalação Automática
        </h1>
        <p className="text-sm mt-1" style={{ color: "#94a3b8" }}>
          Rodada {rodadaAtual} | {mercadoFechado ? "Mercado Fechado" : "Mercado Aberto"}
          {mercadoStatus?.fechamento?.timestamp && (
            <span> | Fechamento: {new Date(mercadoStatus.fechamento.timestamp * 1000).toLocaleString("pt-BR")}</span>
          )}
        </p>
      </div>

      {/* Controls */}
      <div className="rounded-xl p-5" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium" style={{ color: "#f1f5f9" }}>Orçamento (C$)</label>
            <Input
              type="number" value={orcamento} onChange={(e) => setOrcamento(Number(e.target.value))}
              min={50} max={500} step={0.5}
              style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(148, 163, 184, 0.2)", color: "#f1f5f9" }}
            />
            <p className="text-xs" style={{ color: "#64748b" }}>Calculado pela valorização acumulada</p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium" style={{ color: "#f1f5f9" }}>Formação</label>
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
              Escalar Time
            </Button>
          </div>
          <div className="flex items-end">
            <Button onClick={handleSalvar} disabled={!escalacao || salvarMutation.isPending} variant="outline" className="w-full h-10"
              style={{ borderColor: "rgba(52, 211, 153, 0.3)", color: "#34d399" }}>
              {salvarMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Confirmar e Salvar
            </Button>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2 flex-wrap">
          <span className="text-xs px-3 py-1 rounded-full" style={{ background: "rgba(84, 180, 247, 0.15)", color: "#54b4f7", border: "1px solid rgba(84, 180, 247, 0.3)" }}>
            {estrategiaLabel}
          </span>
          {excluirIds.length > 0 && (
            <span className="text-xs px-3 py-1 rounded-full flex items-center gap-1" style={{ background: "rgba(248, 113, 113, 0.1)", color: "#f87171", border: "1px solid rgba(248, 113, 113, 0.3)" }}>
              {excluirIds.length} jogador(es) excluído(s)
              <button onClick={handleResetExcluidos} className="ml-1 hover:opacity-70">×</button>
            </span>
          )}
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
          {/* Stats Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {[
              { label: "PONTUAÇÃO ESPERADA", value: escalacao.pontuacao_esperada?.toFixed(1), color: "#34d399" },
              { label: "CUSTO TOTAL", value: `C$ ${escalacao.custo_total?.toFixed(2)}`, color: "#4da8f0" },
              { label: "SALDO", value: `C$ ${escalacao.orcamento_restante?.toFixed(2)}`, color: "#f1f5f9" },
              { label: "VALORIZAÇÃO TOTAL", value: `${(escalacao.valorizacao_total || 0) >= 0 ? '+' : ''}${(escalacao.valorizacao_total || 0).toFixed(2)}`, color: (escalacao.valorizacao_total || 0) >= 0 ? "#34d399" : "#f87171" },
              { label: "JOGADORES", value: `${escalacao.titulares?.length || 0}`, color: "#94a3b8" },
            ].map((s, i) => (
              <div key={i} className="rounded-lg p-3 text-center" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
                <p className="text-[0.6rem] font-bold tracking-wider mb-1" style={{ color: "#64748b" }}>{s.label}</p>
                <p className="text-lg font-extrabold" style={{ color: s.color }}>{s.value}</p>
              </div>
            ))}
          </div>

          {/* Field Header */}
          <div className="rounded-t-xl flex items-center justify-between flex-wrap gap-3 px-4 py-3"
            style={{ background: "linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9))", border: "1px solid rgba(148, 163, 184, 0.15)", borderBottom: "none" }}>
            <span className="font-extrabold text-lg tracking-wide" style={{ color: "#f1f5f9", fontFamily: "var(--font-heading)" }}>ESCALAÇÃO</span>
            <div className="flex items-center gap-4 flex-wrap">
              <span className="px-3 py-1 rounded-full text-sm font-bold" style={{ background: "rgba(77, 168, 240, 0.15)", color: "#4da8f0", border: "1px solid rgba(77, 168, 240, 0.3)" }}>
                {escalacao.formacao}
              </span>
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
              <div className="relative z-10 flex flex-col justify-evenly h-full py-6">
                <FieldRow jogadores={linhas.ata} capitaoId={escalacao.capitao?.atleta_id} onClickJogador={(id) => setLocation(`/jogador/${id}`)} />
                <FieldRow jogadores={linhas.mei} capitaoId={escalacao.capitao?.atleta_id} onClickJogador={(id) => setLocation(`/jogador/${id}`)} />
                <FieldRow jogadores={linhas.defesa} capitaoId={escalacao.capitao?.atleta_id} onClickJogador={(id) => setLocation(`/jogador/${id}`)} />
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

              <div className="absolute bottom-4 left-4 z-20">
                <span style={{ color: "rgba(255,255,255,0.35)", fontSize: "1.6rem", fontWeight: 800, fontFamily: "var(--font-heading)", letterSpacing: 1 }}>
                  {escalacao.formacao}
                </span>
              </div>
            </div>

            {/* Side List */}
            <div className="flex-[2] rounded-br-xl overflow-y-auto" style={{
              background: "linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.6) 100%)",
              border: "1px solid rgba(148, 163, 184, 0.15)", borderLeft: "none", borderTop: "2px solid rgba(148, 163, 184, 0.15)",
              padding: "8px 12px",
            }}>
              <div className="flex justify-between items-center pb-2 mb-1" style={{ borderBottom: "2px solid rgba(148, 163, 184, 0.2)" }}>
                <div className="flex items-center gap-2">
                  <span className="text-[0.65rem] font-bold tracking-wider" style={{ color: "#64748b", minWidth: 28 }}>POS</span>
                  <span className="text-[0.65rem] font-bold tracking-wider" style={{ color: "#64748b" }}>JOGADOR</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[0.65rem] font-bold tracking-wider" style={{ color: "#4da8f0", minWidth: 60, textAlign: "right" }}>PREÇO</span>
                  <span className="text-[0.65rem] font-bold tracking-wider" style={{ color: "#FFC107", minWidth: 42, textAlign: "right" }}>PREV</span>
                </div>
              </div>
              {titularesOrdenados.map((j: any) => {
                const isCap = escalacao.capitao?.atleta_id === j.atleta_id;
                const pos = POSICOES[j.pos_id] || "?";
                return (
                  <button key={j.atleta_id} onClick={() => setLocation(`/jogador/${j.atleta_id}`)}
                    className="w-full flex justify-between items-center py-1.5 hover:opacity-80"
                    style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}>
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-[0.7rem] font-semibold" style={{ color: "#64748b", minWidth: 28 }}>{pos}</span>
                      {isCap && <span className="inline-flex items-center justify-center rounded-full shrink-0" style={{ width: 16, height: 16, background: "#FFD700", color: "#000", fontSize: "0.55rem", fontWeight: 800 }}>C</span>}
                      <span className="text-[0.8rem] font-bold truncate" style={{ color: "#f1f5f9" }}>{j.apelido?.toUpperCase()}</span>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-[0.75rem] font-semibold" style={{ color: "#4da8f0", minWidth: 60, textAlign: "right" }}>C$ {j.preco?.toFixed(2)}</span>
                      <span className="text-[0.8rem] font-bold" style={{ color: "#FFC107", minWidth: 42, textAlign: "right" }}>{j.pontuacao_esperada?.toFixed(1)}</span>
                    </div>
                  </button>
                );
              })}
              {/* Banco de Reservas */}
              <div className="flex items-center justify-center my-3 gap-2">
                <div className="flex-1 h-px" style={{ background: "rgba(148, 163, 184, 0.2)" }} />
                <span className="text-[0.65rem] font-bold tracking-widest whitespace-nowrap" style={{ color: "#94a3b8" }}>RESERVAS</span>
                <div className="flex-1 h-px" style={{ background: "rgba(148, 163, 184, 0.2)" }} />
              </div>
              <p className="text-[0.6rem] mb-2 px-1" style={{ color: "#64748b", lineHeight: 1.4 }}>
                Entra quando o titular da posição não entrar em campo na rodada.
              </p>
              {escalacao.reservas && Object.entries(escalacao.reservas).map(([posId, reserva]) => {
                if (!reserva) return null;
                const r = reserva as any;
                const pos = POSICOES[Number(posId)] || posId;
                const titularesPos = escalacao.titulares?.filter((t: any) => t.pos_id === Number(posId)) || [];
                const titularNomes = titularesPos.map((t: any) => t.apelido).join(', ');
                return (
                  <div key={posId} className="mb-1">
                    <button onClick={() => setLocation(`/jogador/${r.atleta_id}`)}
                      className="w-full flex justify-between items-center py-1.5 hover:opacity-80"
                      style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}>
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-[0.7rem] font-semibold" style={{ color: "#64748b", minWidth: 28 }}>{pos}</span>
                        <span className="text-[0.8rem] font-bold truncate" style={{ color: "#cbd5e1" }}>{r.apelido?.toUpperCase()}</span>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <span className="text-[0.75rem] font-semibold" style={{ color: "#64748b", minWidth: 60, textAlign: "right" }}>C$ {r.preco?.toFixed(2)}</span>
                        <span className="text-[0.8rem] font-bold" style={{ color: "#64748b", minWidth: 42, textAlign: "right" }}>{(r.pontuacao_esperada || r.score || r.media || 0).toFixed?.(1) ?? '0.0'}</span>
                      </div>
                    </button>
                    {titularNomes && (
                      <p className="text-[0.55rem] px-1 mt-0.5" style={{ color: "#475569" }}>
                        Substitui {titularNomes} se não entrar em campo
                      </p>
                    )}
                  </div>
                );
              })}

              {/* Reserva de Luxo */}
              {escalacao.reserva_luxo && (
                <>
                  <div className="flex items-center justify-center my-3 gap-2">
                    <div className="flex-1 h-px" style={{ background: "rgba(255, 215, 0, 0.2)" }} />
                    <span className="text-[0.65rem] font-bold tracking-widest whitespace-nowrap" style={{ color: "#FFD700" }}>RESERVA DE LUXO</span>
                    <div className="flex-1 h-px" style={{ background: "rgba(255, 215, 0, 0.2)" }} />
                  </div>
                  <p className="text-[0.6rem] mb-2 px-1" style={{ color: "#b8860b", lineHeight: 1.4 }}>
                    Mesma posição do capitão ({POSICOES[escalacao.capitao?.pos_id] || '?'}). Substitui o pior pontuador da posição se fizer mais pontos.
                  </p>
                  <button onClick={() => setLocation(`/jogador/${escalacao.reserva_luxo!.atleta_id}`)}
                    className="w-full flex justify-between items-center py-1.5 hover:opacity-80"
                    style={{ borderBottom: "1px solid rgba(255, 215, 0, 0.1)" }}>
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-[0.7rem] font-semibold" style={{ color: "#FFD700", minWidth: 28 }}>{POSICOES[escalacao.reserva_luxo.pos_id] || "?"}</span>
                      <span className="text-[0.8rem] font-bold truncate" style={{ color: "#FFD700" }}>{escalacao.reserva_luxo.apelido?.toUpperCase()}</span>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-[0.75rem] font-semibold" style={{ color: "#b8860b", minWidth: 60, textAlign: "right" }}>C$ {escalacao.reserva_luxo.preco?.toFixed(2)}</span>
                      <span className="text-[0.8rem] font-bold" style={{ color: "#FFD700", minWidth: 42, textAlign: "right" }}>{(escalacao.reserva_luxo.pontuacao_esperada || escalacao.reserva_luxo.score || escalacao.reserva_luxo.media || 0).toFixed?.(1) ?? '0.0'}</span>
                    </div>
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Capitão + Vice */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {escalacao.capitao && (
              <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(255, 215, 0, 0.2)" }}>
                <h4 className="font-bold mb-3 flex items-center gap-2" style={{ color: "#FFD700" }}>Capitão (x1.5)</h4>
                <button onClick={() => setLocation(`/jogador/${escalacao.capitao!.atleta_id}`)} className="w-full flex items-center justify-between p-2 rounded-lg hover:opacity-80">
                  <div className="flex items-center gap-3">
                    <ClubeBadge clubeId={escalacao.capitao.clube_id} size={24} />
                    <div className="text-left">
                      <p className="font-bold" style={{ color: "#f1f5f9" }}>{escalacao.capitao.apelido}</p>
                      <p className="text-xs" style={{ color: "#94a3b8" }}>{escalacao.capitao.posicao} | {escalacao.capitao.clube || escalacao.capitao.clube_nome}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold" style={{ color: "#FFD700" }}>{(escalacao.capitao.pontuacao_esperada * 1.5).toFixed(1)} pts</p>
                    <p className="text-xs" style={{ color: "#94a3b8" }}>({escalacao.capitao.pontuacao_esperada.toFixed(1)} x 1.5)</p>
                  </div>
                </button>
              </div>
            )}
            {escalacao.vice_capitao && (
              <div className="rounded-xl p-4" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                <h4 className="font-bold mb-3 flex items-center gap-2" style={{ color: "#94a3b8" }}>Vice-Capitão</h4>
                <button onClick={() => setLocation(`/jogador/${escalacao.vice_capitao!.atleta_id}`)} className="w-full flex items-center justify-between p-2 rounded-lg hover:opacity-80">
                  <div className="flex items-center gap-3">
                    <ClubeBadge clubeId={escalacao.vice_capitao.clube_id} size={24} />
                    <div className="text-left">
                      <p className="font-bold" style={{ color: "#f1f5f9" }}>{escalacao.vice_capitao.apelido}</p>
                      <p className="text-xs" style={{ color: "#94a3b8" }}>{escalacao.vice_capitao.posicao} | {escalacao.vice_capitao.clube || escalacao.vice_capitao.clube_nome}</p>
                    </div>
                  </div>
                  <p className="text-lg font-bold" style={{ color: "#cbd5e1" }}>{escalacao.vice_capitao.pontuacao_esperada?.toFixed(1)} pts</p>
                </button>
              </div>
            )}
          </div>

          {/* Detailed Player Cards */}
          <div className="rounded-xl p-5" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold" style={{ color: "#f1f5f9" }}>Detalhes dos Titulares</h3>
              <Button variant="outline" size="sm" onClick={() => {
                if (expandedCards.size > 0) setExpandedCards(new Set());
                else setExpandedCards(new Set(escalacao.titulares.map((j: any) => j.atleta_id)));
              }} style={{ borderColor: "rgba(148, 163, 184, 0.2)", color: "#94a3b8", fontSize: "0.75rem" }}>
                {expandedCards.size > 0 ? "Recolher Todos" : "Expandir Todos"}
              </Button>
            </div>

            {/* Group by position: GOL, ZAG, LAT, MEI, ATA, TEC */}
            {[1, 3, 2, 4, 5, 6].map(posId => {
              const jogadoresPos = escalacao.titulares.filter((j: any) => j.pos_id === posId);
              if (jogadoresPos.length === 0) return null;
              const posNome = POSICOES[posId];
              return (
                <div key={posId} className="mb-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: `${POS_BADGE_COLORS[posNome]}20`, color: POS_BADGE_COLORS[posNome] }}>
                      {posNome}
                    </span>
                  </div>
                  {jogadoresPos.map((j: any) => {
                    const isCap = escalacao.capitao?.atleta_id === j.atleta_id;
                    const isExpanded = expandedCards.has(j.atleta_id);
                    const explicacao = j.explicacao || {};
                    const valorizacao = j.valorizacao_prevista || 0;
                    const isSubbing = substituindo === j.atleta_id;

                    return (
                      <div key={j.atleta_id} className="rounded-lg mb-2 overflow-hidden" style={{
                        background: isCap ? "rgba(255, 215, 0, 0.05)" : "rgba(30, 41, 59, 0.4)",
                        border: `1px solid ${isCap ? "rgba(255, 215, 0, 0.2)" : "rgba(148, 163, 184, 0.1)"}`,
                      }}>
                        {/* Card Header */}
                        <div className="flex items-center justify-between p-3 cursor-pointer" onClick={() => toggleCard(j.atleta_id)}>
                          <div className="flex items-center gap-3">
                            {isCap && <span style={{ fontSize: "1rem" }}>👑</span>}
                            <ClubeBadge clubeId={j.clube_id || 0} size={20} showName={false} />
                            <span className="font-bold" style={{ color: "#f1f5f9" }}>{j.apelido}</span>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-sm font-semibold" style={{ color: "#64748b" }}>C$ {j.preco?.toFixed(2)}</span>
                            <span className="text-sm font-bold" style={{ color: "#f1f5f9" }}>
                              {isCap ? `${(j.pontuacao_esperada * 1.5).toFixed(2)}` : j.pontuacao_esperada?.toFixed(2)} pts
                            </span>
                            <div className="flex items-center gap-1">
                              <span style={{ color: valorizacao >= 0 ? "#34d399" : "#f87171", fontSize: "0.82rem", fontWeight: 600 }}>
                                {valorizacao > 0 ? "▲" : valorizacao < 0 ? "▼" : "◆"} {valorizacao >= 0 ? "+" : ""}{valorizacao.toFixed(2)}
                              </span>
                            </div>
                            {isExpanded ? <ChevronUp size={16} style={{ color: "#94a3b8" }} /> : <ChevronDown size={16} style={{ color: "#94a3b8" }} />}
                          </div>
                        </div>

                        {/* Expanded Details */}
                        {isExpanded && (
                          <div className="px-3 pb-3 space-y-2" style={{ borderTop: "1px solid rgba(148, 163, 184, 0.1)" }}>
                            {/* Explicação */}
                            {explicacao.resumo && (
                              <div className="mt-2">
                                <p className="text-sm font-semibold" style={{
                                  color: explicacao.resumo?.includes("Boa fase") || explicacao.resumo?.includes("premium") ? "#f0b429"
                                    : explicacao.resumo?.includes("queda") ? "#f87171"
                                    : explicacao.resumo?.includes("Aposta") ? "#fbbf24"
                                    : "#94a3b8"
                                }}>
                                  {explicacao.resumo?.includes("Boa fase") || explicacao.resumo?.includes("premium") ? "📈 "
                                    : explicacao.resumo?.includes("queda") ? "📉 "
                                    : explicacao.resumo?.includes("Aposta") ? "🎯 "
                                    : "📋 "}
                                  {explicacao.resumo}
                                </p>
                                {explicacao.significado && (
                                  <p className="text-xs mt-1" style={{ color: "#cbd5e1", lineHeight: 1.5 }}>📝 {explicacao.significado}</p>
                                )}
                                {explicacao.motivo && (
                                  <p className="text-xs mt-1 italic" style={{ color: "#94a3b8", lineHeight: 1.5 }}>💡 {explicacao.motivo}</p>
                                )}
                                {explicacao.analise_medias && (
                                  <p className="text-xs mt-2 pt-2" style={{ color: "#64748b", lineHeight: 1.5, borderTop: "1px solid rgba(77, 168, 240, 0.15)" }}>
                                    📊 {explicacao.analise_medias}
                                  </p>
                                )}
                              </div>
                            )}

                            {/* Substitution + Analysis buttons */}
                            <div className="flex gap-2 mt-2">
                              {isSubbing ? (
                                <>
                                  <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); handleSubstituir(j.atleta_id); }}
                                    style={{ borderColor: "rgba(248, 113, 113, 0.3)", color: "#f87171", fontSize: "0.75rem" }}>
                                    <ArrowRightLeft size={14} className="mr-1" />
                                    Confirmar Remoção
                                  </Button>
                                  <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); handleCancelSubstituicao(); }}
                                    style={{ borderColor: "rgba(148, 163, 184, 0.3)", color: "#94a3b8", fontSize: "0.75rem" }}>
                                    <X size={14} className="mr-1" />
                                    Cancelar
                                  </Button>
                                </>
                              ) : (
                                <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); setSubstituindo(j.atleta_id); }}
                                  style={{ borderColor: "rgba(248, 113, 113, 0.3)", color: "#f87171", fontSize: "0.75rem" }}>
                                  <ArrowRightLeft size={14} className="mr-1" />
                                  Remover e Re-escalar
                                </Button>
                              )}
                              <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); setLocation(`/jogador/${j.atleta_id}`); }}
                                style={{ borderColor: "rgba(77, 168, 240, 0.3)", color: "#4da8f0", fontSize: "0.75rem" }}>
                                Ver Análise
                              </Button>
                            </div>

                            {/* Confirmation message */}
                            {isSubbing && (
                              <div className="mt-2 p-3 rounded-lg" style={{ background: "rgba(248, 113, 113, 0.05)", border: "1px solid rgba(248, 113, 113, 0.2)" }}>
                                <p className="text-xs" style={{ color: "#f87171" }}>
                                  Ao confirmar, {j.apelido} será removido e o time será re-escalado automaticamente com o melhor time possível sem este jogador.
                                </p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>

          {/* Top 10 por Posição */}
          {escalacao.top10PorPosicao && Object.keys(escalacao.top10PorPosicao).length > 0 && (
            <div className="rounded-xl p-5" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
              <div className="flex items-center gap-2 mb-4">
                <Trophy size={20} style={{ color: "#FFD700" }} />
                <h3 className="text-lg font-bold" style={{ color: "#f1f5f9" }}>Top 10 por Posição</h3>
              </div>
              <p className="text-sm mb-4" style={{ color: "#64748b" }}>Melhores jogadores disponíveis em cada posição para esta rodada:</p>

              {/* Position Tabs */}
              <div className="flex gap-1 mb-4 overflow-x-auto pb-1">
                {[1, 2, 3, 4, 5, 6].map(posId => {
                  const posNome = POSICOES[posId];
                  const isActive = activeTop10Tab === posId;
                  return (
                    <button key={posId} onClick={() => setActiveTop10Tab(posId)}
                      className="px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-colors"
                      style={{
                        background: isActive ? `${POS_BADGE_COLORS[posNome]}20` : "rgba(30, 41, 59, 0.4)",
                        color: isActive ? POS_BADGE_COLORS[posNome] : "#64748b",
                        border: `1px solid ${isActive ? `${POS_BADGE_COLORS[posNome]}40` : "rgba(148, 163, 184, 0.1)"}`,
                      }}>
                      {posNome}
                    </button>
                  );
                })}
              </div>

              {/* Top 10 List */}
              <div className="space-y-2">
                {(escalacao.top10PorPosicao[activeTop10Tab] || []).map((j: any, idx: number) => {
                  const rank = idx + 1;
                  const borderColor = rank === 1 ? "#FFD700" : rank === 2 ? "#C0C0C0" : rank === 3 ? "#CD7F32" : "#54b4f7";
                  const rankBadge = rank <= 3 ? ["🥇", "🥈", "🥉"][rank - 1] : `#${rank}`;
                  return (
                    <button key={j.atleta_id} onClick={() => setLocation(`/jogador/${j.atleta_id}`)}
                      className="w-full rounded-lg p-3 hover:opacity-90 transition-opacity text-left"
                      style={{
                        background: "linear-gradient(135deg, rgba(21, 39, 68, 0.8) 0%, rgba(30, 58, 95, 0.8) 100%)",
                        borderLeft: `4px solid ${borderColor}`,
                        border: `1px solid rgba(148, 163, 184, 0.1)`,
                        borderLeftWidth: 4,
                        borderLeftColor: borderColor,
                      }}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-lg">{typeof rankBadge === 'string' && rankBadge.startsWith('#') ?
                            <span className="text-xs font-bold" style={{ color: "#64748b" }}>{rankBadge}</span> : rankBadge}</span>
                          <ClubeBadge clubeId={j.clube_id || 0} size={20} showName={false} />
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-sm" style={{ color: "#f1f5f9" }}>{j.apelido}</span>
                            {j.escalado && (
                              <span className="text-[0.6rem] px-1.5 py-0.5 rounded" style={{ background: "rgba(52, 211, 153, 0.15)", color: "#34d399" }}>Escalado</span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-sm font-semibold" style={{ color: "#f1f5f9" }}>C$ {j.preco?.toFixed(2)}</span>
                          <span className="text-sm font-bold" style={{ color: "#54b4f7" }}>{j.score?.toFixed(2)} pts</span>
                        </div>
                      </div>
                    </button>
                  );
                })}
                {(!escalacao.top10PorPosicao[activeTop10Tab] || escalacao.top10PorPosicao[activeTop10Tab].length === 0) && (
                  <p className="text-sm text-center py-4" style={{ color: "#64748b" }}>Nenhum jogador disponível nesta posição</p>
                )}
              </div>
            </div>
          )}

          {/* Confirm Section */}
          <div className="rounded-xl p-5" style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(52, 211, 153, 0.2)" }}>
            <h3 className="text-lg font-bold mb-2" style={{ color: "#34d399" }}>Confirmar Escalação</h3>
            <p className="text-sm mb-4" style={{ color: "#94a3b8" }}>
              Clique no botão abaixo para salvar a escalação que será utilizada na rodada. Isso registra para o aprendizado contínuo.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Button onClick={handleSalvar} disabled={salvarMutation.isPending} className="h-12"
                style={{ background: "#34d399", color: "#000", fontWeight: 700, fontSize: "1rem" }}>
                {salvarMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Confirmar Escalação Final
              </Button>
              <Button variant="outline" onClick={handleEscalar} disabled={escalarMutation.isPending} className="h-12"
                style={{ borderColor: "rgba(148, 163, 184, 0.3)", color: "#94a3b8" }}>
                Reescalar do Zero
              </Button>
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
      {isCap && (
        <span className="absolute -top-1 -right-1 z-10 flex items-center justify-center rounded-full"
          style={{ width: 16, height: 16, background: "#FFD700", color: "#000", fontSize: "0.55rem", fontWeight: 800 }}>
          C
        </span>
      )}
      <img src={CAMISA_URL} alt="" className="group-hover:scale-110 transition-transform"
        style={{ width: isTec ? 44 : 50, height: isTec ? 48 : 54, objectFit: "contain", filter: `drop-shadow(0 2px 4px rgba(0,0,0,0.5))${isTec ? " brightness(0.85)" : ""}` }} />
      <div className="mt-0.5 text-center rounded px-2 py-0.5" style={{ background: "rgba(0,0,0,0.65)", minWidth: 70 }}>
        <div className="font-bold truncate" style={{ color: "#fff", fontSize: "0.65rem", maxWidth: 90 }}>{apelido}</div>
        <div className="font-semibold" style={{ color: "#4da8f0", fontSize: "0.6rem" }}>C$ {jogador.preco?.toFixed(2)}</div>
      </div>
    </button>
  );
}
