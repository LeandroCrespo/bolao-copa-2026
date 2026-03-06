import { describe, it, expect, afterAll } from "vitest";
import { getNeonPool, neonQuery } from "./neonDb";

afterAll(async () => {
  const pool = getNeonPool();
  await pool.end();
});

// Replicate the calcularValorizacaoComSubstituicoes function for testing
function calcularValorizacaoComSubstituicoes(esc: any): number {
  const jogadores = esc.jogadores || [];
  const reservas = esc.reservas || {};
  const reservaLuxo = esc.reserva_luxo;

  const jogInfo: Record<string, { pontos: number | null; pos_id: number; variacao: number; entrou: boolean; substituido: boolean; subLuxo: boolean }> = {};
  for (const j of jogadores) {
    const aid = String(j.atleta_id || '');
    const pontos = j.pontos_real ?? null;
    jogInfo[aid] = {
      pontos,
      pos_id: j.pos_id,
      variacao: parseFloat(j.variacao || '0') || 0,
      entrou: j.entrou_em_campo ?? (pontos !== null),
      substituido: false,
      subLuxo: false,
    };
  }

  const reservasQueEntraram: any[] = [];
  for (const posIdStr of Object.keys(reservas)) {
    const reserva = reservas[posIdStr];
    if (!reserva) continue;
    const resId = String(reserva.atleta_id || '');
    if (reservaLuxo && resId === String(reservaLuxo.atleta_id || '')) continue;
    const pontosRes = reserva.pontos_real ?? null;
    const resEntrou = reserva.entrou_em_campo ?? (pontosRes !== null);
    const posId = parseInt(posIdStr);
    const tits = Object.entries(jogInfo).filter(([, info]) => info.pos_id === posId && !info.substituido);
    for (const [aid, info] of tits) {
      const titNaoJogou = !info.entrou || info.pontos === null;
      if (titNaoJogou && (resEntrou || pontosRes !== null)) {
        jogInfo[aid].substituido = true;
        reservasQueEntraram.push(reserva);
        break;
      }
    }
  }

  let luxoEntrou = false;
  if (reservaLuxo) {
    const luxoPosId = reservaLuxo.pos_id;
    const pontosLuxo = reservaLuxo.pontos_real ?? null;
    if (pontosLuxo !== null) {
      const tits = Object.entries(jogInfo).filter(([, info]) =>
        info.pos_id === luxoPosId && info.entrou && info.pontos !== null && !info.substituido
      );
      if (tits.length > 0) {
        const pior = tits.reduce((best, cur) => (cur[1].pontos! < best[1].pontos! ? cur : best));
        if (pontosLuxo > pior[1].pontos!) {
          jogInfo[pior[0]].subLuxo = true;
          luxoEntrou = true;
        }
      }
    }
  }

  let val = 0;
  for (const [, info] of Object.entries(jogInfo)) {
    if (!info.substituido && !info.subLuxo) val += info.variacao;
  }
  for (const res of reservasQueEntraram) {
    val += parseFloat(res.variacao || '0') || 0;
  }
  if (luxoEntrou && reservaLuxo) {
    val += parseFloat(reservaLuxo.variacao || '0') || 0;
  }
  return Math.round(val * 100) / 100;
}

describe("calcularValorizacaoComSubstituicoes", () => {
  it("should calculate valorização for all titulares playing", () => {
    const esc = {
      jogadores: [
        { atleta_id: 1, pos_id: 1, pontos_real: 5, variacao: "1.5", entrou_em_campo: true },
        { atleta_id: 2, pos_id: 3, pontos_real: 3, variacao: "-0.5", entrou_em_campo: true },
        { atleta_id: 3, pos_id: 4, pontos_real: 8, variacao: "2.0", entrou_em_campo: true },
      ],
      reservas: {},
      reserva_luxo: null,
    };
    expect(calcularValorizacaoComSubstituicoes(esc)).toBe(3.0);
  });

  it("should substitute titular who did not play with reserve", () => {
    const esc = {
      jogadores: [
        { atleta_id: 1, pos_id: 1, pontos_real: null, variacao: "-1.0", entrou_em_campo: false },
        { atleta_id: 2, pos_id: 3, pontos_real: 3, variacao: "0.5", entrou_em_campo: true },
      ],
      reservas: {
        "1": { atleta_id: 10, pos_id: 1, pontos_real: 4, variacao: "0.8", entrou_em_campo: true },
      },
      reserva_luxo: null,
    };
    // Titular 1 didn't play (-1.0 excluded), reserve enters (+0.8), titular 2 played (+0.5)
    expect(calcularValorizacaoComSubstituicoes(esc)).toBe(1.3);
  });

  it("should apply luxury reserve substitution when it scores more than worst titular", () => {
    const esc = {
      jogadores: [
        { atleta_id: 1, pos_id: 4, pontos_real: 2, variacao: "-0.5", entrou_em_campo: true },
        { atleta_id: 2, pos_id: 4, pontos_real: 10, variacao: "3.0", entrou_em_campo: true },
        { atleta_id: 3, pos_id: 3, pontos_real: 5, variacao: "1.0", entrou_em_campo: true },
      ],
      reservas: {},
      reserva_luxo: { atleta_id: 20, pos_id: 4, pontos_real: 8, variacao: "2.5", entrou_em_campo: true },
    };
    // Luxury reserve (8pts) > worst titular in pos 4 (2pts), so titular 1 excluded (-0.5)
    // Val = titular2(3.0) + titular3(1.0) + luxo(2.5) = 6.5
    expect(calcularValorizacaoComSubstituicoes(esc)).toBe(6.5);
  });

  it("should not apply luxury reserve when it scores less than worst titular", () => {
    const esc = {
      jogadores: [
        { atleta_id: 1, pos_id: 4, pontos_real: 10, variacao: "3.0", entrou_em_campo: true },
        { atleta_id: 2, pos_id: 4, pontos_real: 8, variacao: "2.0", entrou_em_campo: true },
      ],
      reservas: {},
      reserva_luxo: { atleta_id: 20, pos_id: 4, pontos_real: 5, variacao: "1.0", entrou_em_campo: true },
    };
    // Luxury (5pts) < worst titular (8pts), so no substitution
    expect(calcularValorizacaoComSubstituicoes(esc)).toBe(5.0);
  });

  it("should match Streamlit patrimônio calculation from database", async () => {
    // Get the last processed escalação from the database
    const rows = await neonQuery<any>(
      "SELECT escalacao_json, escalacao_json->>'orcamento_disponivel' as orc FROM escalacoes_salvas WHERE ano = 2026 AND atualizado = true ORDER BY rodada DESC LIMIT 1"
    );
    expect(rows.length).toBeGreaterThan(0);
    
    const esc = typeof rows[0].escalacao_json === 'string' ? JSON.parse(rows[0].escalacao_json) : rows[0].escalacao_json;
    const orcDisp = parseFloat(rows[0].orc);
    const val = calcularValorizacaoComSubstituicoes(esc);
    const patrimonio = Math.round((orcDisp + val) * 10) / 10;
    
    // Streamlit shows C$ 113.5 for the current data
    expect(patrimonio).toBe(113.5);
  });
});
