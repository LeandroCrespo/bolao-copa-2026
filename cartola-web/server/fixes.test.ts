import { describe, it, expect, vi } from 'vitest';

// Mock neonDb module
vi.mock('./neonDb', () => ({
  neonQuery: vi.fn(),
  neonQueryOne: vi.fn(),
}));

import { neonQuery, neonQueryOne } from './neonDb';

describe('getHistoricoRodadas', () => {
  it('should query escalacoes_salvas table with correct fields', async () => {
    const { getHistoricoRodadas } = await import('./cartola');
    const mockRows = [
      {
        id: 1,
        rodada: 1,
        ano: 2026,
        formacao: '4-3-3',
        pontos_reais: '75.56',
        valorizacao_real: null,
        atualizado: true,
        data_criacao: '2026-01-29T05:54:42.361Z',
        escalacao_json: {
          jogadores: [{ atleta_id: '123', apelido: 'Test' }],
          pontuacao_prevista: 85.0,
          custo_total: 100.0,
          capitao: { atleta_id: '123', apelido: 'Test' },
        },
      },
    ];
    vi.mocked(neonQuery).mockResolvedValueOnce(mockRows);

    const result = await getHistoricoRodadas(2026);
    expect(result).toEqual(mockRows);
    expect(neonQuery).toHaveBeenCalledWith(
      expect.stringContaining('escalacoes_salvas'),
      [2026]
    );
    expect(neonQuery).toHaveBeenCalledWith(
      expect.stringContaining('escalacao_json'),
      expect.anything()
    );
  });
});

describe('getDbStats', () => {
  it('should count escalacoes_salvas instead of escalacoes', async () => {
    const { getDbStats } = await import('./cartola');
    vi.mocked(neonQueryOne).mockResolvedValueOnce({
      jogadores: '145196',
      rodadas: '76',
      escalacoes: '41',
      jogadores_stats: '0',
    });

    const result = await getDbStats();
    expect(result.escalacoes_salvas).toBe(41);
    expect(neonQueryOne).toHaveBeenCalledWith(
      expect.stringContaining('escalacoes_salvas'),
    );
  });
});

describe('getPartidas', () => {
  it('should include valida field in partidas response', async () => {
    const { getPartidas } = await import('./cartola');
    // This function calls the Cartola API, so we need to mock axios
    const axios = await import('axios');
    vi.spyOn(axios.default, 'get').mockResolvedValueOnce({
      data: {
        partidas: [
          {
            partida_id: 1,
            clube_casa_id: 262,
            clube_visitante_id: 263,
            placar_oficial_mandante: 2,
            placar_oficial_visitante: 1,
            valida: true,
            partida_data: '2026-03-08T16:00:00-03:00',
          },
          {
            partida_id: 2,
            clube_casa_id: 264,
            clube_visitante_id: 265,
            placar_oficial_mandante: null,
            placar_oficial_visitante: null,
            valida: false,
            partida_data: '2026-03-09T18:30:00-03:00',
          },
        ],
      },
    });

    const result = await getPartidas(5);
    expect(result.length).toBe(2);
    expect(result[0]).toHaveProperty('valida', true);
    expect(result[1]).toHaveProperty('valida', false);
  });
});
