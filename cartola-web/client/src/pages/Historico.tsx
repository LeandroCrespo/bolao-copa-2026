import { useState, useMemo } from "react";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, Area, AreaChart, ComposedChart, Cell, PieChart, Pie,
  ScatterChart, Scatter
} from "recharts";

// ===== POSICOES & COLORS =====
const POSICOES: Record<number, string> = { 1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC" };
const POS_COLORS: Record<string, string> = { GOL: "#FFC107", ZAG: "#54b4f7", LAT: "#34d399", MEI: "#a78bfa", ATA: "#f87171", TEC: "#94a3b8" };

function ClubeBadge({ clubeId, size = 20 }: { clubeId: number; size?: number }) {
  return <img src={`https://s.sde.globo.com/media/organizations/${clubeId}/2025/04/18/escudo_60x60.png`} width={size} height={size} className="inline-block" alt="" />;
}

function MiniStat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="rounded-lg p-2 text-center" style={{ background: "rgba(30, 41, 59, 0.5)" }}>
      <p className="text-[10px]" style={{ color: "#64748b" }}>{label}</p>
      <p className="text-sm font-bold" style={{ color }}>{value}</p>
    </div>
  );
}

// ===== REFERENCE DATA 2025 =====
const REF_FIXO: Record<number, { pts: number; orc: number }> = {
  1:{pts:30.6,orc:100.0},2:{pts:87.0,orc:87.8},3:{pts:56.4,orc:98.0},4:{pts:107.8,orc:102.1},
  5:{pts:86.3,orc:115.7},6:{pts:96.0,orc:122.2},7:{pts:101.9,orc:128.1},8:{pts:99.5,orc:136.2},
  9:{pts:66.1,orc:137.4},10:{pts:41.5,orc:130.0},11:{pts:102.8,orc:126.9},12:{pts:85.9,orc:130.1},
  13:{pts:74.6,orc:134.0},14:{pts:94.5,orc:129.6},15:{pts:96.9,orc:136.0},16:{pts:70.2,orc:138.1},
  17:{pts:71.3,orc:142.1},18:{pts:95.2,orc:141.7},19:{pts:102.4,orc:150.1},20:{pts:90.6,orc:153.9},
  21:{pts:161.5,orc:155.4},22:{pts:79.9,orc:160.7},23:{pts:99.5,orc:157.9},24:{pts:86.7,orc:159.3},
  25:{pts:103.5,orc:163.4},26:{pts:94.1,orc:169.9},27:{pts:94.5,orc:170.3},28:{pts:126.1,orc:170.9},
  29:{pts:124.2,orc:178.5},30:{pts:116.1,orc:181.2},31:{pts:89.2,orc:191.6},32:{pts:128.0,orc:193.8},
  33:{pts:70.1,orc:200.7},34:{pts:114.2,orc:196.6},35:{pts:127.5,orc:204.4},36:{pts:121.7,orc:207.3},
  37:{pts:107.7,orc:216.0},38:{pts:121.1,orc:218.2},
};
const REF_AUTO: Record<number, { pts: number; orc: number; formacao: string }> = {
  1:{pts:34.1,orc:100.0,formacao:'4-4-2'},2:{pts:88.0,orc:97.1,formacao:'4-4-2'},
  3:{pts:73.8,orc:106.1,formacao:'4-5-1'},4:{pts:100.7,orc:114.1,formacao:'4-3-3'},
  5:{pts:81.9,orc:123.7,formacao:'4-5-1'},6:{pts:101.2,orc:128.3,formacao:'4-5-1'},
  7:{pts:116.1,orc:135.9,formacao:'4-4-2'},8:{pts:104.9,orc:145.8,formacao:'4-4-2'},
  9:{pts:50.5,orc:146.0,formacao:'4-4-2'},10:{pts:50.1,orc:140.8,formacao:'3-5-2'},
  11:{pts:103.9,orc:138.7,formacao:'4-3-3'},12:{pts:79.6,orc:140.5,formacao:'4-3-3'},
  13:{pts:76.8,orc:140.6,formacao:'3-4-3'},14:{pts:98.6,orc:138.4,formacao:'4-3-3'},
  15:{pts:108.1,orc:145.5,formacao:'4-4-2'},16:{pts:77.2,orc:149.2,formacao:'4-4-2'},
  17:{pts:67.5,orc:154.2,formacao:'4-3-3'},18:{pts:98.0,orc:153.4,formacao:'4-3-3'},
  19:{pts:105.5,orc:158.2,formacao:'4-5-1'},20:{pts:98.4,orc:161.3,formacao:'4-3-3'},
  21:{pts:173.5,orc:164.6,formacao:'4-3-3'},22:{pts:92.4,orc:170.9,formacao:'4-4-2'},
  23:{pts:105.8,orc:170.6,formacao:'4-3-3'},24:{pts:84.5,orc:173.0,formacao:'4-4-2'},
  25:{pts:103.5,orc:175.2,formacao:'4-3-3'},26:{pts:94.1,orc:181.7,formacao:'4-3-3'},
  27:{pts:101.9,orc:182.1,formacao:'4-4-2'},28:{pts:126.1,orc:184.1,formacao:'4-3-3'},
  29:{pts:124.2,orc:191.7,formacao:'4-3-3'},30:{pts:116.1,orc:194.4,formacao:'4-3-3'},
  31:{pts:89.2,orc:204.8,formacao:'4-3-3'},32:{pts:126.4,orc:207.1,formacao:'4-4-2'},
  33:{pts:70.1,orc:213.5,formacao:'4-3-3'},34:{pts:114.2,orc:209.4,formacao:'4-3-3'},
  35:{pts:117.9,orc:217.2,formacao:'4-4-2'},36:{pts:127.5,orc:219.5,formacao:'4-4-2'},
  37:{pts:107.7,orc:229.1,formacao:'4-3-3'},38:{pts:122.1,orc:231.2,formacao:'4-5-1'},
};
const MARCOS_FIXO = { media_r1_r5: 73.6, media_r6_r15: 86.0, media_r16_r25: 96.1, media_r26_r38: 110.3, media_geral: 95.3, total: 3623.1 };
const MARCOS_AUTO = { media_r1_r5: 75.7, media_r6_r15: 89.0, media_r16_r25: 100.6, media_r26_r38: 110.6, media_geral: 97.7, total: 3712.1 };
const CUSTO_MEDIO_IDEAL_2025 = 107.6;
const CUSTO_MEDIO_FIXO180 = 160.9;

const APROV_REF_FIXO: Record<number, number> = {
  1:18.4,2:42.0,3:43.2,4:50.6,5:50.8,6:53.5,7:54.9,8:54.3,9:52.5,10:49.7,
  11:50.3,12:50.5,13:49.8,14:50.7,15:50.6,16:50.4,17:50.0,18:50.3,19:50.3,20:50.2,
  21:51.2,22:51.3,23:51.4,24:51.5,25:51.6,26:51.6,27:51.8,28:52.3,29:52.9,30:53.2,
  31:53.2,32:53.9,33:53.4,34:53.8,35:54.4,36:54.5,37:54.4,38:54.6,
};
const APROV_REF_AUTO: Record<number, number> = {
  1:21.1,2:42.2,3:46.3,4:50.6,5:51.2,6:53.5,7:55.8,8:55.1,9:53.5,10:52.3,
  11:50.8,12:51.2,13:51.0,14:50.6,15:51.5,16:52.0,17:52.0,18:52.0,19:51.4,20:51.9,
  21:52.0,22:51.9,23:53.1,24:53.4,25:53.6,26:53.6,27:53.5,28:53.8,29:54.3,30:54.8,
  31:55.1,32:55.0,33:55.6,34:55.1,35:55.5,36:55.8,37:56.1,38:55.9,
};

// ===== MAIN COMPONENT =====
export default function Historico() {
  const [ano] = useState(2026);
  const [expandedRodada, setExpandedRodada] = useState<number | null>(null);
  const { data: escalacoes, isLoading } = trpc.db.historicoRodadas.useQuery({ ano });
  const rodadasProcessadasList = useMemo(() => {
    if (!escalacoes) return [];
    return escalacoes.filter((e: any) => e.pontos_reais != null && Number(e.pontos_reais) > 0).map((e: any) => e.rodada);
  }, [escalacoes]);
  const { data: pontosIdeais } = trpc.db.pontosIdeaisBatch.useQuery(
    { ano, rodadas: rodadasProcessadasList },
    { enabled: rodadasProcessadasList.length > 0 }
  );

  const parsedRows = useMemo(() => {
    if (!escalacoes) return [];
    return escalacoes.map((e: any) => {
      const esc = typeof e.escalacao_json === "string" ? JSON.parse(e.escalacao_json) : e.escalacao_json;
      return {
        rodada: e.rodada,
        pontos_reais: e.pontos_reais != null ? Number(e.pontos_reais) : null,
        esc,
        formacao: e.formacao || esc?.formacao || "?",
        data_criacao: e.data_criacao,
        orcamento: esc?.orcamento_disponivel || 100,
        previsto: esc?.pontuacao_prevista || 0,
      };
    }).sort((a: any, b: any) => a.rodada - b.rodada);
  }, [escalacoes]);

  // Calculate key metrics
  const metrics = useMemo(() => {
    const processadas = parsedRows.filter((r: any) => r.pontos_reais != null && r.pontos_reais > 0);
    const totalReal = processadas.reduce((s: number, r: any) => s + r.pontos_reais, 0);
    const mediaReal = processadas.length > 0 ? totalReal / processadas.length : 0;
    const ultimaRodada = parsedRows.length > 0 ? parsedRows[parsedRows.length - 1].rodada : 0;
    const orcAtual = parsedRows.length > 0 ? parsedRows[parsedRows.length - 1].orcamento : 100;

    // Compare with ref_fixo and ref_auto for same rounds
    const rodadas2026 = processadas.map((r: any) => r.rodada);
    const ptsFixoMesmas = rodadas2026.map((r: number) => REF_FIXO[r]?.pts || 0).filter((v: number) => v > 0);
    const ptsAutoMesmas = rodadas2026.map((r: number) => REF_AUTO[r]?.pts || 0).filter((v: number) => v > 0);
    const mediaFixoMesmas = ptsFixoMesmas.length > 0 ? ptsFixoMesmas.reduce((a: number, b: number) => a + b, 0) / ptsFixoMesmas.length : 0;
    const mediaAutoMesmas = ptsAutoMesmas.length > 0 ? ptsAutoMesmas.reduce((a: number, b: number) => a + b, 0) / ptsAutoMesmas.length : 0;

    const diffPctFixo = mediaFixoMesmas > 0 ? ((mediaReal - mediaFixoMesmas) / mediaFixoMesmas * 100) : 0;
    const diffPctAuto = mediaAutoMesmas > 0 ? ((mediaReal - mediaAutoMesmas) / mediaAutoMesmas * 100) : 0;

    let statusEmoji: string, statusTexto: string, statusCor: string;
    if (diffPctFixo > 10 && diffPctAuto > 10) {
      statusEmoji = "🟢"; statusTexto = "ACIMA de ambas referências 2025"; statusCor = "#28A745";
    } else if (diffPctFixo < -10 && diffPctAuto < -10) {
      statusEmoji = "🔴"; statusTexto = "ABAIXO de ambas referências 2025"; statusCor = "#DC3545";
    } else if (diffPctFixo > 10 || diffPctAuto > 10) {
      statusEmoji = "🟢"; statusTexto = "ACIMA de pelo menos uma referência 2025"; statusCor = "#28A745";
    } else if (diffPctFixo < -10 || diffPctAuto < -10) {
      statusEmoji = "🟡"; statusTexto = "DENTRO do padrão (entre as referências)"; statusCor = "#FFC107";
    } else {
      statusEmoji = "🟡"; statusTexto = "DENTRO do padrão 2025"; statusCor = "#FFC107";
    }

    // Calculate aproveitamento using pontosIdeais
    let aproveitamento = 0;
    if (pontosIdeais && processadas.length > 0) {
      const totalIdeal = processadas.reduce((s: number, r: any) => s + (pontosIdeais[r.rodada] || 0), 0);
      aproveitamento = totalIdeal > 0 ? (totalReal / totalIdeal) * 100 : 0;
    }

    return {
      processadas, totalReal, mediaReal, ultimaRodada, orcAtual,
      rodadas2026, mediaFixoMesmas, mediaAutoMesmas, diffPctFixo, diffPctAuto,
      statusEmoji, statusTexto, statusCor, aproveitamento,
    };
  }, [parsedRows, pontosIdeais]);

  const { processadas, totalReal, mediaReal, ultimaRodada, orcAtual, rodadas2026,
    mediaFixoMesmas, mediaAutoMesmas, diffPctFixo, diffPctAuto,
    statusEmoji, statusTexto, statusCor, aproveitamento } = metrics;

  // ===== CHART DATA (all hooks must be before conditional returns) =====
  // 1. Desempenho por Rodada (bars green/red + line previsto)
  const desempenhoData = useMemo(() => parsedRows.map((r: any) => ({
    rodada: `R${r.rodada}`,
    real: r.pontos_reais || 0,
    previsto: r.previsto,
    media: mediaReal,
    isPositive: (r.pontos_reais || 0) >= mediaReal,
  })), [parsedRows, mediaReal]);

  // 2. Pontuação: 2026 vs Referências 2025 (line chart with projection)
  const pontuacaoCompData = useMemo(() => {
    const data: any[] = [];
    for (let r = 1; r <= 38; r++) {
      const row2026 = parsedRows.find((p: any) => p.rodada === r);
      const pts2026 = row2026?.pontos_reais && row2026.pontos_reais > 0 ? row2026.pontos_reais : null;
      data.push({
        rodada: r,
        real2026: pts2026,
        fixo2025: REF_FIXO[r]?.pts || null,
        auto2025: REF_AUTO[r]?.pts || null,
        projecao: null,
      });
    }
    // Add projection
    if (ultimaRodada > 0 && ultimaRodada < 38 && processadas.length > 0) {
      const ptsAutoMesmasRodadas = rodadas2026.map((r: number) => REF_AUTO[r]?.pts || 0).filter((v: number) => v > 0);
      const mediaAutoMesmasR = ptsAutoMesmasRodadas.length > 0 ? ptsAutoMesmasRodadas.reduce((a: number, b: number) => a + b, 0) / ptsAutoMesmasRodadas.length : 1;
      const fatorAjuste = mediaAutoMesmasR > 0 ? mediaReal / mediaAutoMesmasR : 1.0;
      const ultimaPts = processadas[processadas.length - 1].pontos_reais;
      if (data[ultimaRodada - 1]) data[ultimaRodada - 1].projecao = ultimaPts;
      for (let r = ultimaRodada + 1; r <= 38; r++) {
        const ptsRef = REF_AUTO[r]?.pts || mediaReal;
        data[r - 1].projecao = ptsRef * fatorAjuste;
      }
    }
    return data;
  }, [parsedRows, ultimaRodada, processadas, rodadas2026, mediaReal]);

  // 3. Evolução do Orçamento: 2026 vs 2025
  const orcamentoCompData = useMemo(() => {
    const orcPorRodada: Record<number, number> = {};
    for (const r of parsedRows) orcPorRodada[r.rodada] = r.orcamento;
    const data: any[] = [];
    for (let r = 1; r <= 38; r++) {
      data.push({
        rodada: r,
        orc2026: orcPorRodada[r] || null,
        fixo2025: REF_FIXO[r]?.orc || null,
        auto2025: REF_AUTO[r]?.orc || null,
        projecao: null,
      });
    }
    // Projection
    if (ultimaRodada > 0 && ultimaRodada < 38) {
      const orcRefMesma = REF_AUTO[ultimaRodada]?.orc || 100;
      const orcRealUltima = orcPorRodada[ultimaRodada] || orcAtual;
      const fatorOrc = orcRefMesma > 0 ? orcRealUltima / orcRefMesma : 1.0;
      if (data[ultimaRodada - 1]) data[ultimaRodada - 1].projecao = orcRealUltima;
      for (let r = ultimaRodada + 1; r <= 38; r++) {
        const orcRef = REF_AUTO[r]?.orc || (data[r - 2]?.projecao || orcAtual) + 3.5;
        data[r - 1].projecao = orcRef * fatorOrc;
      }
    }
    return data;
  }, [parsedRows, ultimaRodada, orcAtual]);

  // 4. Aproveitamento: 2026 vs 2025
  const aprovCompData = useMemo(() => {
    // We need pts_ideal for each round - use timeIdeal query results
    // For now, calculate from the processadas data
    const data: any[] = [];
    let acumReal = 0;
    let acumIdeal = 0;
    for (let r = 1; r <= 38; r++) {
      const row2026 = processadas.find((p: any) => p.rodada === r);
      let aprov2026: number | null = null;
      if (row2026) {
        acumReal += row2026.pontos_reais ?? 0;
        // We'll estimate ideal as real / aproveitamento_ref_auto[r] * 100
        // But better: we need actual ideal points. For now use a rough estimate.
      }
      data.push({
        rodada: r,
        fixo2025: APROV_REF_FIXO[r] || null,
        auto2025: APROV_REF_AUTO[r] || null,
        aprov2026: null, // Will be filled by timeIdeal data
        projecao: null,
      });
    }
    return data;
  }, [processadas]);

  // 5. Comparação Detalhada table data
  const comparacaoData = useMemo(() => parsedRows.filter((r: any) => r.pontos_reais != null && r.pontos_reais > 0).map((r: any) => {
    const ptsFixo = REF_FIXO[r.rodada]?.pts || 0;
    const ptsAuto = REF_AUTO[r.rodada]?.pts || 0;
    const diffFixo = r.pontos_reais - ptsFixo;
    const diffAuto = r.pontos_reais - ptsAuto;
    let status: string;
    if (diffFixo > 10 && diffAuto > 10) status = "🟢";
    else if (diffFixo < -10 && diffAuto < -10) status = "🔴";
    else status = "🟡";
    return {
      rodada: r.rodada,
      pts2026: r.pontos_reais,
      ptsFixo, ptsAuto, diffFixo, diffAuto,
      orc2026: r.orcamento,
      status,
    };
  }), [parsedRows]);

  // 6. Aproveitamento por Posição
  const aprovPosData = useMemo(() => {
    const posStats: Record<string, { real: number; ideal: number; count: number }> = {};
    // This needs timeIdeal data per round - we'll calculate from escalacao data
    for (const r of processadas) {
      const jogadores = r.esc?.jogadores || [];
      for (const j of jogadores) {
        const posNome = POSICOES[j.pos_id || j.posicao_id] || "?";
        if (!posStats[posNome]) posStats[posNome] = { real: 0, ideal: 0, count: 0 };
        posStats[posNome].real += (j.pontos_real ?? j.pontos_reais ?? 0);
        posStats[posNome].count++;
      }
    }
    return Object.entries(posStats).map(([pos, stats]) => {
      const media = stats.count > 0 ? stats.real / stats.count : 0;
      // Color based on performance: green if >= 5, yellow if >= 3, red if < 3
      let fill = "#f87171"; // red
      if (media >= 5) fill = "#34d399"; // green
      else if (media >= 3) fill = "#FFC107"; // yellow
      return { pos, media, count: stats.count, fill };
    });
  }, [processadas]);

  // 7. Distribuição de Justificativas
  const justificativasData = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const r of parsedRows) {
      const jogadores = r.esc?.jogadores || [];
      for (const j of jogadores) {
        // Use explicacao.resumo or explicacao.tendencia as the justificativa category
        const expl = j.explicacao || {};
        const just = expl.resumo || expl.tendencia || expl.motivo || "Sem justificativa";
        // Simplify to category: extract the first emoji+text pattern
        const cat = just.split("|")[0].trim();
        counts[cat] = (counts[cat] || 0) + 1;
      }
    }
    const COLORS = ["#54b4f7", "#34d399", "#FFC107", "#f87171", "#a78bfa", "#FF69B4", "#94a3b8", "#fb923c"];
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([name, value], i) => ({ name, value, fill: COLORS[i % COLORS.length] }));
  }, [parsedRows]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2" style={{ borderColor: "#54b4f7" }} />
      </div>
    );
  }

  if (!parsedRows.length) {
    return (
      <div className="container py-8 text-center" style={{ color: "#94a3b8" }}>
        <p className="text-xl">Nenhuma escalação salva para {ano}</p>
      </div>
    );
  }

  return (
    <div className="container py-6 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold" style={{ color: "#f1f5f9" }}>
          📊 Histórico de Resultados — {ano}
        </h2>
        <p className="text-sm mt-1" style={{ color: "#94a3b8" }}>
          {parsedRows.length} rodadas escaladas • {processadas.length} processadas
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MiniStat label="Total de Pontos" value={totalReal.toFixed(1)} color="#54b4f7" />
        <MiniStat label="Média por Rodada" value={mediaReal.toFixed(1)} color="#FFC107" />
        <MiniStat label="Aproveitamento" value={aproveitamento > 0 ? `${aproveitamento.toFixed(1)}%` : "—"} color="#34d399" />
        <MiniStat label="Orçamento Atual" value={`C$ ${orcAtual.toFixed(1)}`} color="#a78bfa" />
      </div>

      {/* Diagnostic Card */}
      <div className="rounded-xl p-4" style={{
        background: 'linear-gradient(135deg, #1a2744 0%, #0b1d33 100%)',
        borderLeft: `4px solid ${statusCor}`,
      }}>
        <div className="flex items-center gap-3">
          <span className="text-3xl">{statusEmoji}</span>
          <div>
            <h4 className="font-bold" style={{ color: statusCor }}>{statusTexto}</h4>
            <p className="text-xs mt-1" style={{ color: "#94a3b8" }}>
              Rodada {ultimaRodada} de 38 — {processadas.length} rodadas com dados
            </p>
          </div>
        </div>
        <p className="text-sm mt-2" style={{ color: "#e0e0e0" }}>
          Média 2026: <strong style={{ color: "#54b4f7" }}>{mediaReal.toFixed(1)} pts</strong> | 
          Ref. 4-3-3 fixo: <strong>{mediaFixoMesmas.toFixed(1)} pts</strong> ({diffPctFixo >= 0 ? "+" : ""}{diffPctFixo.toFixed(1)}%) | 
          Ref. automática: <strong>{mediaAutoMesmas.toFixed(1)} pts</strong> ({diffPctAuto >= 0 ? "+" : ""}{diffPctAuto.toFixed(1)}%)
        </p>
      </div>

      {/* Tabs for charts */}
      <Tabs defaultValue="desempenho" className="w-full">
        <TabsList className="w-full flex flex-wrap h-auto gap-1" style={{ background: "rgba(15, 23, 42, 0.6)" }}>
          <TabsTrigger value="desempenho" className="text-xs">Desempenho</TabsTrigger>
          <TabsTrigger value="pontuacao" className="text-xs">Pontuação 2026 vs 2025</TabsTrigger>
          <TabsTrigger value="orcamento" className="text-xs">Orçamento 2026 vs 2025</TabsTrigger>
          <TabsTrigger value="aproveitamento" className="text-xs">Aproveitamento 2026 vs 2025</TabsTrigger>
          <TabsTrigger value="posicao" className="text-xs">Por Posição</TabsTrigger>
          <TabsTrigger value="justificativas" className="text-xs">Justificativas</TabsTrigger>
        </TabsList>

        {/* Tab 1: Desempenho por Rodada */}
        <TabsContent value="desempenho">
          <Card style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
            <CardHeader><CardTitle className="text-sm" style={{ color: "#f1f5f9" }}>📊 Desempenho por Rodada</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <ComposedChart data={desempenhoData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="rodada" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", color: "#f1f5f9" }} />
                  <Legend />
                  <ReferenceLine y={mediaReal} stroke="#FFC107" strokeDasharray="5 5" label={{ value: `Média: ${mediaReal.toFixed(1)}`, fill: "#FFC107", fontSize: 10 }} />
                  <Bar dataKey="real" name="Pontos Reais" radius={[4, 4, 0, 0]}>
                    {desempenhoData.map((entry: any, index: number) => (
                      <Cell key={index} fill={entry.isPositive ? "#28A745" : "#DC3545"} />
                    ))}
                  </Bar>
                  <Line type="monotone" dataKey="previsto" name="Previsto" stroke="#FFC107" strokeDasharray="5 5" strokeWidth={2} dot={{ r: 3, fill: "#FFC107" }} />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: Pontuação 2026 vs Referências 2025 */}
        <TabsContent value="pontuacao">
          <Card style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
            <CardHeader><CardTitle className="text-sm" style={{ color: "#f1f5f9" }}>📊 Pontuação: 2026 vs Referências 2025</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={pontuacaoCompData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="rodada" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", color: "#f1f5f9" }} />
                  <Legend />
                  <Line type="monotone" dataKey="fixo2025" name="2025 — 4-3-3 Fixo" stroke="#FF69B4" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 3, fill: "#FF69B4" }} connectNulls={false} />
                  <Line type="monotone" dataKey="auto2025" name="2025 — Automática" stroke="#98FB98" strokeWidth={2} strokeDasharray="8 4" dot={{ r: 3, fill: "#98FB98" }} connectNulls={false} />
                  <Line type="monotone" dataKey="real2026" name="2026 (Real)" stroke="#54b4f7" strokeWidth={3} dot={{ r: 5, fill: "#54b4f7" }} connectNulls={false} />
                  <Line type="monotone" dataKey="projecao" name="Projeção 2026" stroke="#54b4f7" strokeWidth={2} strokeDasharray="5 5" opacity={0.5} dot={false} connectNulls={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: Evolução do Orçamento 2026 vs 2025 */}
        <TabsContent value="orcamento">
          <Card style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
            <CardHeader><CardTitle className="text-sm" style={{ color: "#f1f5f9" }}>💰 Evolução do Orçamento: 2026 vs Referências 2025</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={orcamentoCompData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="rodada" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", color: "#f1f5f9" }} />
                  <Legend />
                  <ReferenceLine y={CUSTO_MEDIO_IDEAL_2025} stroke="#FFC107" strokeDasharray="5 5" label={{ value: `Custo médio ideal: C$ ${CUSTO_MEDIO_IDEAL_2025}`, fill: "#FFC107", fontSize: 10, position: "insideBottomLeft" }} />
                  <ReferenceLine y={CUSTO_MEDIO_FIXO180} stroke="#FF69B4" strokeDasharray="5 5" label={{ value: `Custo fixo 180: C$ ${CUSTO_MEDIO_FIXO180}`, fill: "#FF69B4", fontSize: 10, position: "insideTopLeft" }} />
                  <Line type="monotone" dataKey="fixo2025" name="2025 — 4-3-3 Fixo" stroke="#FF69B4" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 3, fill: "#FF69B4" }} connectNulls={false} />
                  <Line type="monotone" dataKey="auto2025" name="2025 — Automática" stroke="#98FB98" strokeWidth={2} strokeDasharray="8 4" dot={{ r: 3, fill: "#98FB98" }} connectNulls={false} />
                  <Line type="monotone" dataKey="orc2026" name="2026 (Real)" stroke="#54b4f7" strokeWidth={3} dot={{ r: 5, fill: "#54b4f7" }} connectNulls={false} />
                  <Line type="monotone" dataKey="projecao" name="Projeção 2026" stroke="#54b4f7" strokeWidth={2} strokeDasharray="5 5" opacity={0.5} dot={false} connectNulls={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 4: Aproveitamento 2026 vs 2025 */}
        <TabsContent value="aproveitamento">
          <AproveitamentoChart parsedRows={parsedRows} processadas={processadas} ultimaRodada={ultimaRodada} ano={ano} />
        </TabsContent>

        {/* Tab 5: Aproveitamento por Posição */}
        <TabsContent value="posicao">
          <Card style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
            <CardHeader><CardTitle className="text-sm" style={{ color: "#f1f5f9" }}>📊 Aproveitamento por Posição</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={aprovPosData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <YAxis dataKey="pos" type="category" tick={{ fill: "#94a3b8", fontSize: 11 }} width={40} />
                  <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", color: "#f1f5f9" }}
                    formatter={(value: any) => [`${Number(value).toFixed(1)} pts/jogo`, "Média"]} />
                  <ReferenceLine x={5} stroke="#28A745" strokeDasharray="5 5" label={{ value: "Meta", fill: "#28A745", fontSize: 10 }} />
                  <Bar dataKey="media" name="Média pts/jogo" radius={[0, 4, 4, 0]}>
                    {aprovPosData.map((entry: any, index: number) => (
                      <Cell key={index} fill={entry.media >= 5 ? "#28A745" : entry.media >= 3 ? "#FFC107" : "#DC3545"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 6: Distribuição de Justificativas */}
        <TabsContent value="justificativas">
          <Card style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
            <CardHeader><CardTitle className="text-sm" style={{ color: "#f1f5f9" }}>📊 Distribuição de Justificativas</CardTitle></CardHeader>
            <CardContent>
              <div className="flex flex-col md:flex-row items-center gap-4">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie data={justificativasData} cx="50%" cy="50%" innerRadius={60} outerRadius={110}
                      paddingAngle={2} dataKey="value" nameKey="name"
                      label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                      labelLine={{ stroke: "#94a3b8" }}>
                      {justificativasData.map((entry: any, index: number) => (
                        <Cell key={index} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", color: "#f1f5f9" }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Comparação Detalhada por Rodada */}
      <Card style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
        <CardHeader><CardTitle className="text-sm" style={{ color: "#f1f5f9" }}>📋 Comparação Detalhada por Rodada</CardTitle></CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-xs" style={{ borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "#1a2744", color: "#fff" }}>
                  <th className="p-2 text-center" style={{ borderBottom: "2px solid #54b4f7" }}>Rod.</th>
                  <th className="p-2 text-center" style={{ borderBottom: "2px solid #54b4f7" }}>2026</th>
                  <th className="p-2 text-center" style={{ borderBottom: "2px solid #54b4f7" }}>2025 Fixo</th>
                  <th className="p-2 text-center" style={{ borderBottom: "2px solid #54b4f7" }}>Dif. Fixo</th>
                  <th className="p-2 text-center" style={{ borderBottom: "2px solid #54b4f7" }}>2025 Auto</th>
                  <th className="p-2 text-center" style={{ borderBottom: "2px solid #54b4f7" }}>Dif. Auto</th>
                  <th className="p-2 text-center" style={{ borderBottom: "2px solid #54b4f7" }}>Orç. 2026</th>
                  <th className="p-2 text-center" style={{ borderBottom: "2px solid #54b4f7" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {comparacaoData.map((row: any, i: number) => (
                  <tr key={row.rodada} style={{ background: i % 2 === 0 ? "#0b1d33" : "#111d33", color: "#e0e0e0" }}>
                    <td className="p-1.5 text-center font-bold">R{row.rodada}</td>
                    <td className="p-1.5 text-center font-bold" style={{ color: "#54b4f7" }}>{row.pts2026.toFixed(1)}</td>
                    <td className="p-1.5 text-center" style={{ color: "#ADB5BD" }}>{row.ptsFixo.toFixed(1)}</td>
                    <td className="p-1.5 text-center font-bold" style={{ color: row.diffFixo > 10 ? "#28A745" : row.diffFixo < -10 ? "#DC3545" : "#FFC107" }}>
                      {row.diffFixo >= 0 ? "+" : ""}{row.diffFixo.toFixed(1)}
                    </td>
                    <td className="p-1.5 text-center" style={{ color: "#ADB5BD" }}>{row.ptsAuto.toFixed(1)}</td>
                    <td className="p-1.5 text-center font-bold" style={{ color: row.diffAuto > 10 ? "#28A745" : row.diffAuto < -10 ? "#DC3545" : "#FFC107" }}>
                      {row.diffAuto >= 0 ? "+" : ""}{row.diffAuto.toFixed(1)}
                    </td>
                    <td className="p-1.5 text-center">C$ {row.orc2026.toFixed(1)}</td>
                    <td className="p-1.5 text-center">{row.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Projeções e Expectativas */}
      <ProjecoesSection parsedRows={parsedRows} processadas={processadas} ultimaRodada={ultimaRodada} orcAtual={orcAtual} totalReal={totalReal} />

      {/* Detalhes por Rodada */}
      <div>
        <h3 className="text-lg font-bold mb-3" style={{ color: "#f1f5f9" }}>📋 Detalhes por Rodada</h3>
        <div className="space-y-2">
          {[...parsedRows].reverse().map((e: any) => (
            <RodadaDetail
              key={e.rodada}
              e={e}
              isExpanded={expandedRodada === e.rodada}
              onToggle={() => setExpandedRodada(expandedRodada === e.rodada ? null : e.rodada)}
              ano={ano}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// ===== APROVEITAMENTO CHART (needs timeIdeal data) =====
function AproveitamentoChart({ processadas, ultimaRodada }: { parsedRows: any[]; processadas: any[]; ultimaRodada: number; ano: number }) {
  // Calculate aproveitamento using pontuacao_ideal from escalacao data
  // The aproveitamento is: pontos_reais_acumulados / pontos_ideal_acumulados * 100
  const chartData = useMemo(() => {
    let acumReal = 0;
    let acumIdeal = 0;
    const aprovData: { rodada: number; aprov2026: number }[] = [];

    for (const r of processadas) {
      const ptsReal = r.pontos_reais || 0;
      // Use pontuacao_ideal from escalacao_json if available, otherwise estimate
      const ptsIdeal = r.esc?.pontuacao_ideal || r.esc?.pontuacao_time_ideal || (ptsReal / (APROV_REF_AUTO[r.rodada] || 50) * 100);
      acumReal += ptsReal;
      acumIdeal += ptsIdeal;
      const aprov = acumIdeal > 0 ? (acumReal / acumIdeal * 100) : 0;
      aprovData.push({ rodada: r.rodada, aprov2026: aprov });
    }

    const data: any[] = [];
    for (let r = 1; r <= 38; r++) {
      const a26 = aprovData.find(a => a.rodada === r);
      data.push({
        rodada: r,
        fixo2025: APROV_REF_FIXO[r] || null,
        auto2025: APROV_REF_AUTO[r] || null,
        aprov2026: a26?.aprov2026 || null,
        projecao: null,
      });
    }

    // Projection
    if (aprovData.length > 0 && ultimaRodada < 38) {
      const lastAprov = aprovData[aprovData.length - 1].aprov2026;
      const autoMesma = APROV_REF_AUTO[ultimaRodada] || 50;
      const diffAprov = lastAprov - autoMesma;
      data[ultimaRodada - 1].projecao = lastAprov;
      for (let r = ultimaRodada + 1; r <= 38; r++) {
        const projetado = (APROV_REF_AUTO[r] || 55) + diffAprov;
        data[r - 1].projecao = Math.min(100, Math.max(0, projetado));
      }
    }

    return data;
  }, [processadas, ultimaRodada]);

  const aprovAtual = chartData.find(d => d.rodada === ultimaRodada)?.aprov2026;

  return (
    <Card style={{ background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
      <CardHeader>
        <CardTitle className="text-sm" style={{ color: "#f1f5f9" }}>
          📊 Aproveitamento: 2026 vs Referências 2025
          {aprovAtual != null && <span className="ml-2 text-xs" style={{ color: "#54b4f7" }}>({aprovAtual.toFixed(1)}%)</span>}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="rodada" tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} domain={[0, 100]} />
            <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", color: "#f1f5f9" }}
              formatter={(value: any) => [`${Number(value).toFixed(1)}%`, ""]} />
            <Legend />
            <ReferenceLine y={50} stroke="#28A745" strokeDasharray="5 5" label={{ value: "Meta: 50%", fill: "#28A745", fontSize: 10 }} />
            <Line type="monotone" dataKey="fixo2025" name="2025 — 4-3-3 Fixo" stroke="#FF69B4" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 3, fill: "#FF69B4" }} connectNulls={false} />
            <Line type="monotone" dataKey="auto2025" name="2025 — Automática" stroke="#98FB98" strokeWidth={2} strokeDasharray="8 4" dot={{ r: 3, fill: "#98FB98" }} connectNulls={false} />
            <Line type="monotone" dataKey="aprov2026" name="2026 (Real)" stroke="#54b4f7" strokeWidth={3} dot={{ r: 5, fill: "#54b4f7" }} connectNulls={false} />
            <Line type="monotone" dataKey="projecao" name="Projeção 2026" stroke="#54b4f7" strokeWidth={2} strokeDasharray="5 5" opacity={0.5} dot={false} connectNulls={false} />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

// ===== PROJECOES SECTION =====
function ProjecoesSection({ parsedRows, processadas, ultimaRodada, orcAtual, totalReal }: {
  parsedRows: any[]; processadas: any[]; ultimaRodada: number; orcAtual: number; totalReal: number;
}) {
  // Determine current phase
  let faseAtual: string, faseCor: string, faseEmoji: string;
  let expFixo: number, expAuto: number;
  let proximaFase: string, proxFixo: number, proxAuto: number, rodadasParaProxima: number;

  if (ultimaRodada <= 5) {
    faseAtual = "Fase Inicial"; faseCor = "#DC3545"; faseEmoji = "🚀";
    expFixo = MARCOS_FIXO.media_r1_r5; expAuto = MARCOS_AUTO.media_r1_r5;
    proximaFase = "Crescimento (R6-R15)";
    proxFixo = MARCOS_FIXO.media_r6_r15; proxAuto = MARCOS_AUTO.media_r6_r15;
    rodadasParaProxima = Math.max(0, 6 - ultimaRodada);
  } else if (ultimaRodada <= 15) {
    faseAtual = "Crescimento"; faseCor = "#FFC107"; faseEmoji = "📈";
    expFixo = MARCOS_FIXO.media_r6_r15; expAuto = MARCOS_AUTO.media_r6_r15;
    proximaFase = "Consolidação (R16-R25)";
    proxFixo = MARCOS_FIXO.media_r16_r25; proxAuto = MARCOS_AUTO.media_r16_r25;
    rodadasParaProxima = Math.max(0, 16 - ultimaRodada);
  } else if (ultimaRodada <= 25) {
    faseAtual = "Consolidação"; faseCor = "#28A745"; faseEmoji = "⚡";
    expFixo = MARCOS_FIXO.media_r16_r25; expAuto = MARCOS_AUTO.media_r16_r25;
    proximaFase = "Maturidade (R26-R38)";
    proxFixo = MARCOS_FIXO.media_r26_r38; proxAuto = MARCOS_AUTO.media_r26_r38;
    rodadasParaProxima = Math.max(0, 26 - ultimaRodada);
  } else {
    faseAtual = "Maturidade"; faseCor = "#54b4f7"; faseEmoji = "🏆";
    expFixo = MARCOS_FIXO.media_r26_r38; expAuto = MARCOS_AUTO.media_r26_r38;
    proximaFase = "Final da temporada";
    proxFixo = MARCOS_FIXO.media_r26_r38; proxAuto = MARCOS_AUTO.media_r26_r38;
    rodadasParaProxima = Math.max(0, 38 - ultimaRodada);
  }

  // Projeção de pontuação
  const ptsRestFixo = Array.from({ length: 38 - ultimaRodada }, (_, i) => REF_FIXO[ultimaRodada + 1 + i]?.pts || 0).reduce((a, b) => a + b, 0);
  const ptsRestAuto = Array.from({ length: 38 - ultimaRodada }, (_, i) => REF_AUTO[ultimaRodada + 1 + i]?.pts || 0).reduce((a, b) => a + b, 0);
  const projFixo = totalReal + ptsRestFixo;
  const projAuto = totalReal + ptsRestAuto;
  const pctTemporada = (ultimaRodada / 38) * 100;

  // Marcos de orçamento
  function estimarRodadasPara(alvo: number): string {
    if (orcAtual >= alvo) return `✅ Já alcançado (C$ ${orcAtual.toFixed(0)})`;
    if (parsedRows.length >= 2) {
      const orcPrimeiro = parsedRows[0].orcamento;
      const rAtual = parsedRows[parsedRows.length - 1].rodada;
      const taxa = (orcAtual - orcPrimeiro) / Math.max(1, rAtual - 1);
      if (taxa > 0) {
        const rodadas = Math.ceil((alvo - orcAtual) / taxa);
        return `~${rodadas} rodadas (R${Math.min(38, rAtual + rodadas)})`;
      }
    }
    const taxa2025 = (REF_FIXO[38].orc - 100) / 37;
    if (taxa2025 > 0) {
      const rodadas = Math.ceil((alvo - orcAtual) / taxa2025);
      return `~${rodadas} rodadas (est. 2025)`;
    }
    return "Dados insuficientes";
  }

  const textoIdeal = estimarRodadasPara(CUSTO_MEDIO_IDEAL_2025);
  const textoFixo180 = estimarRodadasPara(CUSTO_MEDIO_FIXO180);

  // Insight text
  function getInsightText() {
    if (ultimaRodada <= 5) {
      return (
        <p style={{ color: "#e0e0e0", lineHeight: 1.6 }}>
          Você está na <strong>fase inicial</strong> da temporada. Em 2025, o Modelo Dervé FC fez em média{" "}
          <strong>{MARCOS_FIXO.media_r1_r5.toFixed(0)} pts</strong> (4-3-3) e <strong>{MARCOS_AUTO.media_r1_r5.toFixed(0)} pts</strong> (automática){" "}
          nas primeiras rodadas, subindo para <strong>{Math.min(MARCOS_FIXO.media_r6_r15, MARCOS_AUTO.media_r6_r15).toFixed(0)} a {Math.max(MARCOS_FIXO.media_r6_r15, MARCOS_AUTO.media_r6_r15).toFixed(0)} pts</strong>{" "}
          entre as rodadas 6-15.
          <br /><br />
          <strong>Padrão observado:</strong> A formação automática superou o 4-3-3 fixo em 2025{" "}
          ({MARCOS_AUTO.total.toFixed(0)} vs {MARCOS_FIXO.total.toFixed(0)} pts, +{(MARCOS_AUTO.total - MARCOS_FIXO.total).toFixed(0)} pts).{" "}
          A flexibilidade de formação permite aproveitar melhor os jogadores disponíveis a cada rodada.
          O orçamento cresce gradualmente, permitindo escalações melhores a cada rodada.
          <br /><br />
          <strong>Marcos:</strong> Em 2025, o orçamento alcançou o custo médio do time ideal (C$ {CUSTO_MEDIO_IDEAL_2025.toFixed(0)}) na R4.{" "}
          {orcAtual >= CUSTO_MEDIO_IDEAL_2025
            ? `Em 2026, esse marco foi atingido (C$ ${orcAtual.toFixed(0)}).`
            : `Em 2026, o orçamento atual é C$ ${orcAtual.toFixed(0)}.`}
          {" "}A partir da R26-R33, as escalações tendem a se igualar às do orçamento fixo de C$ 180.
        </p>
      );
    }
    if (ultimaRodada <= 15) {
      return (
        <p style={{ color: "#e0e0e0", lineHeight: 1.6 }}>
          O modelo está acumulando dados de 2026 e melhorando as previsões. Em 2025, a média subiu de{" "}
          <strong>{Math.min(MARCOS_FIXO.media_r1_r5, MARCOS_AUTO.media_r1_r5).toFixed(0)} a {Math.max(MARCOS_FIXO.media_r1_r5, MARCOS_AUTO.media_r1_r5).toFixed(0)}</strong> para{" "}
          <strong>{Math.min(MARCOS_FIXO.media_r6_r15, MARCOS_AUTO.media_r6_r15).toFixed(0)} a {Math.max(MARCOS_FIXO.media_r6_r15, MARCOS_AUTO.media_r6_r15).toFixed(0)} pts/rodada</strong> nesta fase.
          <br /><br />
          <strong>Expectativa:</strong> Média de {Math.min(MARCOS_FIXO.media_r6_r15, MARCOS_AUTO.media_r6_r15).toFixed(0)} a {Math.max(MARCOS_FIXO.media_r6_r15, MARCOS_AUTO.media_r6_r15).toFixed(0)} pts/rodada.
          A formação automática tende a superar o 4-3-3 fixo (+{(MARCOS_AUTO.total - MARCOS_FIXO.total).toFixed(0)} pts na temporada completa).
          A partir da R16, espera-se a fase de consolidação.
        </p>
      );
    }
    if (ultimaRodada <= 25) {
      return (
        <p style={{ color: "#e0e0e0", lineHeight: 1.6 }}>
          O modelo está maduro e o orçamento permite escalações competitivas. Em 2025, a média foi de{" "}
          <strong>{Math.min(MARCOS_FIXO.media_r16_r25, MARCOS_AUTO.media_r16_r25).toFixed(0)} a {Math.max(MARCOS_FIXO.media_r16_r25, MARCOS_AUTO.media_r16_r25).toFixed(0)} pts/rodada</strong> nesta fase.
          <br /><br />
          <strong>Expectativa:</strong> A partir da R26, o orçamento deve ser suficiente para escalar o mesmo time{" "}
          que o orçamento fixo de C$ 180, com média de {Math.min(MARCOS_FIXO.media_r26_r38, MARCOS_AUTO.media_r26_r38).toFixed(0)} a {Math.max(MARCOS_FIXO.media_r26_r38, MARCOS_AUTO.media_r26_r38).toFixed(0)} pts/rodada.
        </p>
      );
    }
    return (
      <p style={{ color: "#e0e0e0", lineHeight: 1.6 }}>
        O orçamento está no nível máximo e as escalações são equivalentes às do orçamento fixo de C$ 180.
        Em 2025, a média foi de <strong>{Math.min(MARCOS_FIXO.media_r26_r38, MARCOS_AUTO.media_r26_r38).toFixed(0)} a {Math.max(MARCOS_FIXO.media_r26_r38, MARCOS_AUTO.media_r26_r38).toFixed(0)} pts/rodada</strong>.
        <br /><br />
        <strong>Foco:</strong> Maximizar pontuação rodada a rodada. O orçamento não é mais limitante.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold" style={{ color: "#f1f5f9" }}>🔮 Projeções e Expectativas</h3>

      <div className="grid md:grid-cols-3 gap-4">
        {/* Card 1: Fase Atual */}
        <div className="rounded-xl p-5 text-center" style={{
          background: 'linear-gradient(135deg, #1a2744 0%, #0b1d33 100%)',
          borderTop: `3px solid ${faseCor}`,
        }}>
          <span className="text-4xl">{faseEmoji}</span>
          <h4 className="font-bold mt-2 mb-1" style={{ color: faseCor }}>{faseAtual}</h4>
          <p className="text-xs" style={{ color: '#94a3b8' }}>Rodada {ultimaRodada} de 38</p>
          <hr className="my-3" style={{ borderColor: 'rgba(255,255,255,0.1)' }} />
          <p className="text-xs" style={{ color: '#e0e0e0' }}>
            <strong>Expectativa (4-3-3):</strong> {expFixo.toFixed(0)} pts/rodada
          </p>
          <p className="text-xs mt-1" style={{ color: '#e0e0e0' }}>
            <strong>Expectativa (Auto):</strong> {expAuto.toFixed(0)} pts/rodada
          </p>
          <p className="text-xs mt-2" style={{ color: '#54b4f7' }}>
            Próxima fase em {rodadasParaProxima} rodada(s):<br />
            {proximaFase} → {Math.min(proxFixo, proxAuto).toFixed(0)}-{Math.max(proxFixo, proxAuto).toFixed(0)} pts
          </p>
        </div>

        {/* Card 2: Projeção da Temporada */}
        <div className="rounded-xl p-5 text-center" style={{
          background: 'linear-gradient(135deg, #1a2744 0%, #0b1d33 100%)',
          borderTop: '3px solid #54b4f7',
        }}>
          <span className="text-4xl">📊</span>
          <h4 className="font-bold mt-2 mb-1" style={{ color: '#54b4f7' }}>Projeção da Temporada</h4>
          <p className="text-xs" style={{ color: '#94a3b8' }}>{pctTemporada.toFixed(0)}% concluída</p>
          <hr className="my-3" style={{ borderColor: 'rgba(255,255,255,0.1)' }} />
          <p className="text-xs" style={{ color: '#e0e0e0' }}>
            <strong>Acumulado 2026:</strong> {totalReal.toFixed(0)} pts
          </p>
          <p className="text-xs mt-1" style={{ color: '#e0e0e0' }}>
            <strong>Projeção (ref. 4-3-3):</strong> ~{projFixo.toFixed(0)} pts
          </p>
          <p className="text-xs mt-1" style={{ color: '#e0e0e0' }}>
            <strong>Projeção (ref. Auto):</strong> ~{projAuto.toFixed(0)} pts
          </p>
          <hr className="my-3" style={{ borderColor: 'rgba(255,255,255,0.1)' }} />
          <p className="text-xs" style={{ color: '#FFC107' }}>
            Ref. 2025: 4-3-3 = {MARCOS_FIXO.total.toFixed(0)} | Auto = {MARCOS_AUTO.total.toFixed(0)}
          </p>
        </div>

        {/* Card 3: Marcos de Orçamento */}
        <div className="rounded-xl p-5 text-center" style={{
          background: 'linear-gradient(135deg, #1a2744 0%, #0b1d33 100%)',
          borderTop: '3px solid #28A745',
        }}>
          <span className="text-4xl">💰</span>
          <h4 className="font-bold mt-2 mb-1" style={{ color: '#28A745' }}>Marcos de Orçamento</h4>
          <p className="text-xs" style={{ color: '#94a3b8' }}>Atual: C$ {orcAtual.toFixed(1)}</p>
          <hr className="my-3" style={{ borderColor: 'rgba(255,255,255,0.1)' }} />
          <p className="text-xs" style={{ color: '#e0e0e0' }}>
            🎯 Time ideal (C$ {CUSTO_MEDIO_IDEAL_2025}): {textoIdeal}
          </p>
          <p className="text-xs mt-2" style={{ color: '#e0e0e0' }}>
            🏆 Fixo 180 (C$ {CUSTO_MEDIO_FIXO180}): {textoFixo180}
          </p>
        </div>
      </div>

      {/* Insight */}
      <div className="rounded-xl p-5" style={{
        background: 'linear-gradient(135deg, #1a2744 0%, #0b1d33 100%)',
        borderLeft: `4px solid ${faseCor}`,
      }}>
        <h4 className="font-bold mb-3" style={{ color: faseCor }}>
          💡 O que esperar nas próximas rodadas
        </h4>
        <div className="text-sm">
          {getInsightText()}
        </div>
      </div>
    </div>
  );
}

// ===== RODADA DETAIL COMPONENT =====
function RodadaDetail({ e, isExpanded, onToggle, ano }: { e: any; isExpanded: boolean; onToggle: () => void; ano: number }) {
  const esc = e.esc;
  const pontosReais = e.pontos_reais != null ? Number(e.pontos_reais) : null;
  const pontosPrev = esc?.pontuacao_prevista || 0;
  const diff = pontosReais != null ? pontosReais - pontosPrev : null;
  const formacao = e.formacao || esc?.formacao || "?";
  const capitao = esc?.capitao;
  const capitaoId = esc?.capitao_id || (capitao ? String(capitao.atleta_id) : null);
  const jogadores = esc?.jogadores || [];
  const processado = esc?.processado === true || (pontosReais != null && pontosReais > 0);
  const orcDisp = esc?.orcamento_disponivel || 100;

  const { data: timeIdeal } = trpc.db.timeIdeal.useQuery(
    { ano, rodada: e.rodada, orcamento: Number(orcDisp), formacao },
    { enabled: isExpanded && processado }
  );

  const jogadoresByPos: Record<number, any[]> = {};
  for (const j of jogadores) {
    const posId = j.pos_id || j.posicao_id || 0;
    if (!jogadoresByPos[posId]) jogadoresByPos[posId] = [];
    jogadoresByPos[posId].push(j);
  }

  let valorizacao = 0;
  for (const j of jogadores) { valorizacao += (j.variacao || 0); }

  const idsEscalados = new Set(jogadores.map((j: any) => String(j.atleta_id)));
  const acertosIdeal = timeIdeal?.titulares?.filter((t: any) => idsEscalados.has(String(t.atleta_id))).length || 0;
  const ptsIdeal = timeIdeal?.pontuacao_real || 0;
  const aprovRodada = ptsIdeal > 0 && pontosReais != null ? (pontosReais / ptsIdeal * 100) : 0;

  // Check for ajustes automáticos
  const ajustes = esc?.ajustes_automaticos || esc?.historico_ajustes || [];

  return (
    <div className="rounded-xl overflow-hidden transition-all"
      style={{
        background: "rgba(15, 23, 42, 0.6)",
        border: isExpanded ? "1px solid rgba(84, 180, 247, 0.3)" : "1px solid rgba(148, 163, 184, 0.1)",
      }}>
      <button className="w-full text-left p-4 transition-colors hover:bg-white/[0.02]" onClick={onToggle}>
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="rounded-lg p-2 text-center min-w-[55px]" style={{ background: "rgba(84, 180, 247, 0.1)" }}>
              <p className="text-[10px]" style={{ color: "#64748b" }}>Rodada</p>
              <p className="text-lg font-bold" style={{ color: "#54b4f7" }}>{e.rodada}</p>
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: "rgba(148, 163, 184, 0.1)", color: "#94a3b8" }}>{formacao}</span>
                {processado && <span className="text-[10px] font-bold px-2 py-0.5 rounded" style={{ background: "rgba(52, 211, 153, 0.15)", color: "#34d399" }}>✅ Processada</span>}
                {!processado && <span className="text-[10px] font-bold px-2 py-0.5 rounded" style={{ background: "rgba(234, 179, 8, 0.15)", color: "#EAB308" }}>⏳ Aguardando</span>}
                {capitao && <span className="text-xs" style={{ color: "#94a3b8" }}>Cap: <strong style={{ color: "#EAB308" }}>{capitao.apelido}</strong></span>}
                {ajustes.length > 0 && <span className="text-[10px] font-bold px-2 py-0.5 rounded" style={{ background: "rgba(168, 85, 247, 0.15)", color: "#a78bfa" }}>🔧 Ajuste automático</span>}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-lg font-bold" style={{ color: processado ? "#54b4f7" : "#64748b" }}>
                {processado && pontosReais != null ? pontosReais.toFixed(1) : "—"}
              </p>
              <p className="text-[10px]" style={{ color: "#64748b" }}>Real</p>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold" style={{ color: "#FFC107" }}>{pontosPrev.toFixed(1)}</p>
              <p className="text-[10px]" style={{ color: "#64748b" }}>Previsto</p>
            </div>
            {diff != null && processado && (
              <div className="text-right min-w-[45px]">
                <p className="text-sm font-bold" style={{ color: diff >= 0 ? "#34d399" : "#f87171" }}>
                  {diff >= 0 ? "+" : ""}{diff.toFixed(1)}
                </p>
              </div>
            )}
            <span style={{ color: "#64748b" }}>{isExpanded ? "▲" : "▼"}</span>
          </div>
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4" style={{ borderTop: "1px solid rgba(148, 163, 184, 0.1)" }}>
          {/* Ajustes automáticos */}
          {ajustes.length > 0 && (
            <div className="mt-3 rounded-lg p-3" style={{ background: "rgba(168, 85, 247, 0.08)", border: "1px solid rgba(168, 85, 247, 0.2)" }}>
              <p className="text-xs font-bold mb-1" style={{ color: "#a78bfa" }}>🔧 Ajustes Automáticos Aplicados:</p>
              {ajustes.map((aj: any, i: number) => (
                <p key={i} className="text-xs" style={{ color: "#e0e0e0" }}>
                  • {aj.descricao || aj.tipo || JSON.stringify(aj)}
                </p>
              ))}
            </div>
          )}

          {/* Comparison: Escalação vs Time Ideal */}
          {processado && timeIdeal && (
            <div className="mt-3 grid md:grid-cols-2 gap-4">
              {/* Left: Our Team */}
              <div className="rounded-xl p-3" style={{ background: "rgba(30, 41, 59, 0.3)", border: "1px solid rgba(84, 180, 247, 0.2)" }}>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-bold" style={{ color: "#54b4f7" }}>⚽ Escalação Sugerida</p>
                  <span className="text-sm font-bold" style={{ color: "#54b4f7" }}>{pontosReais?.toFixed(1)} pts</span>
                </div>
                <div className="grid grid-cols-3 gap-2 mb-2">
                  <MiniStat label="Pts Real" value={pontosReais?.toFixed(1) || '—'} color="#54b4f7" />
                  <MiniStat label="Aproveitamento" value={`${aprovRodada.toFixed(0)}%`} color={aprovRodada >= 50 ? '#34d399' : '#f87171'} />
                  <MiniStat label="Acertos" value={`${acertosIdeal}/${timeIdeal.titulares?.length || 12}`} color="#FFC107" />
                </div>
                {[1, 3, 2, 4, 5, 6].map((posId) => {
                  const posJogadores = jogadoresByPos[posId];
                  if (!posJogadores || posJogadores.length === 0) return null;
                  const posNome = POSICOES[posId] || "?";
                  const posColor = POS_COLORS[posNome] || "#94a3b8";
                  return (
                    <div key={posId} className="mb-1">
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ background: `${posColor}20`, color: posColor }}>{posNome}</span>
                      {posJogadores.map((j: any) => {
                        const isCapitao = j.e_capitao || (capitaoId && String(j.atleta_id) === String(capitaoId));
                        const ptsReal = j.pontos_real ?? j.pontos_reais;
                        const wasInIdeal = timeIdeal.titulares?.some((t: any) => String(t.atleta_id) === String(j.atleta_id));
                        return (
                          <div key={j.atleta_id} className="flex items-center justify-between px-2 py-1 text-xs rounded mt-0.5"
                            style={{ background: wasInIdeal ? "rgba(52, 211, 153, 0.05)" : "rgba(30, 41, 59, 0.3)" }}>
                            <div className="flex items-center gap-1.5">
                              {j.clube_id && <ClubeBadge clubeId={j.clube_id} size={14} />}
                              <span style={{ color: "#f1f5f9" }}>{j.apelido}</span>
                              {isCapitao && <span className="text-[8px] px-1 rounded" style={{ background: "rgba(234, 179, 8, 0.2)", color: "#EAB308" }}>C</span>}
                              {wasInIdeal && <span className="text-[8px] px-1 rounded" style={{ background: "rgba(52, 211, 153, 0.15)", color: "#34d399" }}>✓</span>}
                            </div>
                            <div className="flex items-center gap-2">
                              <span style={{ color: "#4da8f0" }}>C$ {(j.preco || 0).toFixed(1)}</span>
                              {ptsReal != null && <span className="font-bold" style={{ color: Number(ptsReal) >= 0 ? "#34d399" : "#f87171" }}>{Number(ptsReal).toFixed(1)}</span>}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>

              {/* Right: Ideal Team */}
              <div className="rounded-xl p-3" style={{ background: "rgba(30, 41, 59, 0.3)", border: "1px solid rgba(52, 211, 153, 0.2)" }}>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-bold" style={{ color: "#34d399" }}>🏆 Melhor Time Possível</p>
                  <span className="text-sm font-bold" style={{ color: "#34d399" }}>{ptsIdeal.toFixed(1)} pts</span>
                </div>
                <div className="grid grid-cols-2 gap-2 mb-2">
                  <MiniStat label="Pontuação" value={ptsIdeal.toFixed(1)} color="#34d399" />
                  <MiniStat label="Custo" value={`C$ ${(timeIdeal.custo_total || 0).toFixed(1)}`} color="#a78bfa" />
                </div>
                {[1, 3, 2, 4, 5, 6].map((posId) => {
                  const idealPos = timeIdeal.titulares?.filter((t: any) => t.pos_id === posId) || [];
                  if (idealPos.length === 0) return null;
                  const posNome = POSICOES[posId] || "?";
                  const posColor = POS_COLORS[posNome] || "#94a3b8";
                  return (
                    <div key={posId} className="mb-1">
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ background: `${posColor}20`, color: posColor }}>{posNome}</span>
                      {idealPos.map((t: any) => {
                        const wasEscalado = idsEscalados.has(String(t.atleta_id));
                        const isCap = timeIdeal.capitao && String(t.atleta_id) === String(timeIdeal.capitao.atleta_id);
                        return (
                          <div key={t.atleta_id} className="flex items-center justify-between px-2 py-1 text-xs rounded mt-0.5"
                            style={{ background: wasEscalado ? "rgba(52, 211, 153, 0.05)" : "rgba(248, 113, 113, 0.03)" }}>
                            <div className="flex items-center gap-1.5">
                              {t.clube_id && <ClubeBadge clubeId={t.clube_id} size={14} />}
                              <span style={{ color: "#f1f5f9" }}>{t.apelido}</span>
                              {isCap && <span className="text-[8px] px-1 rounded" style={{ background: "rgba(234, 179, 8, 0.2)", color: "#EAB308" }}>C</span>}
                              {wasEscalado ? (
                                <span className="text-[8px] px-1 rounded" style={{ background: "rgba(52, 211, 153, 0.15)", color: "#34d399" }}>✓ Escalado</span>
                              ) : (
                                <span className="text-[8px] px-1 rounded" style={{ background: "rgba(248, 113, 113, 0.1)", color: "#f87171" }}>✗</span>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <span style={{ color: "#4da8f0" }}>C$ {(t.preco || 0).toFixed(1)}</span>
                              <span className="font-bold" style={{ color: "#FFC107" }}>{t.pontos.toFixed(1)}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
                {timeIdeal.capitao && (
                  <p className="text-[10px] mt-2" style={{ color: "#EAB308" }}>
                    👑 Capitão ideal: <strong>{timeIdeal.capitao.apelido}</strong>
                  </p>
                )}
              </div>
            </div>
          )}

          {!processado && jogadores.length > 0 && (
            <div className="mt-3 space-y-2">
              {[1, 3, 2, 4, 5, 6].map((posId) => {
                const posJogadores = jogadoresByPos[posId];
                if (!posJogadores || posJogadores.length === 0) return null;
                const posNome = POSICOES[posId] || "?";
                const posColor = POS_COLORS[posNome] || "#94a3b8";
                return (
                  <div key={posId}>
                    <span className="text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ background: `${posColor}20`, color: posColor }}>{posNome}</span>
                    {posJogadores.map((j: any) => (
                      <div key={j.atleta_id} className="flex items-center justify-between px-2 py-1 text-xs rounded mt-0.5"
                        style={{ background: "rgba(30, 41, 59, 0.3)" }}>
                        <div className="flex items-center gap-1.5">
                          {j.clube_id && <ClubeBadge clubeId={j.clube_id} size={14} />}
                          <span style={{ color: "#f1f5f9" }}>{j.apelido}</span>
                        </div>
                        <span style={{ color: "#FFC107" }}>Prev: {(j.score_previsto || j.pontuacao_esperada || 0).toFixed(1)}</span>
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          )}

          <p className="text-[10px] mt-3" style={{ color: "#475569" }}>
            Salvo em: {e.data_criacao ? new Date(e.data_criacao).toLocaleString("pt-BR") : "—"}
          </p>
        </div>
      )}
    </div>
  );
}
