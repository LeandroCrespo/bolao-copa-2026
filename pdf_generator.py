import os
from fpdf import FPDF
from datetime import datetime
import pytz

def get_brazil_time_str(dt):
    """Converte datetime para string no fuso de Brasília"""
    if not dt:
        return "N/A"
    # Assume que o dt do banco está em UTC
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    br_tz = pytz.timezone('America/Sao_Paulo')
    dt_br = dt.astimezone(br_tz)
    return dt_br.strftime("%d/%m/%Y %H:%M")


def remove_emojis(text):
    """Remove emojis e caracteres Unicode não suportados pela fonte padrão"""
    if not text:
        return ""
    # Mantém apenas caracteres ASCII e Latin-1 estendido
    return ''.join(c for c in str(text) if ord(c) < 0x10000 and c.isprintable())


class PredictionPDF(FPDF):
    def __init__(self):
        super().__init__()
        # Usa fonte padrão Helvetica que suporta Latin-1
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, 'COMPROVANTE DE PALPITES', 0, 0, 'C')
        self.ln(6)
        self.set_font('Helvetica', '', 10)
        self.cell(0, 10, 'Bolao Copa do Mundo 2026', 0, 0, 'C')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.cell(0, 10, f'Pagina {self.page_no()} | Gerado em {now_str}', 0, 0, 'C')


def generate_user_backup_pdf(user_name, match_predictions, group_predictions, podium_prediction):
    """
    Gera o PDF de backup com todos os palpites do usuário.
    Retorna os bytes do PDF.
    """
    pdf = PredictionPDF()
    pdf.add_page()

    # Informações do Usuário
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, f'Participante: {remove_emojis(user_name)}', 0, 1)
    pdf.set_font('Helvetica', '', 9)
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pdf.cell(0, 6, f'Documento gerado em: {now_str}', 0, 1)
    pdf.ln(5)

    # =========================================================================
    # SEÇÃO PÓDIO
    # =========================================================================
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 9, '  PALPITE DE PODIO', 1, 1, 'L', True)
    pdf.set_font('Helvetica', '', 10)

    if podium_prediction:
        pdf.cell(0, 7, f"  Campeao: {remove_emojis(podium_prediction['champion'])}", 0, 1)
        pdf.cell(0, 7, f"  Vice-Campeao: {remove_emojis(podium_prediction['runner_up'])}", 0, 1)
        pdf.cell(0, 7, f"  3o Lugar: {remove_emojis(podium_prediction['third_place'])}", 0, 1)
        pdf.set_font('Helvetica', 'I', 8)
        pdf.cell(0, 7, f"  Salvo em: {podium_prediction['updated_at']}", 0, 1)
    else:
        pdf.cell(0, 7, "  Nenhum palpite de podio registrado.", 0, 1)
    pdf.ln(5)

    # =========================================================================
    # SEÇÃO GRUPOS
    # =========================================================================
    pdf.set_fill_color(200, 255, 220)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 9, '  PALPITES DE CLASSIFICACAO DOS GRUPOS', 1, 1, 'L', True)
    pdf.ln(2)

    if group_predictions:
        # Cabeçalho da tabela
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(20, 7, 'Grupo', 1, 0, 'C')
        pdf.cell(60, 7, '1o Colocado', 1, 0, 'C')
        pdf.cell(60, 7, '2o Colocado', 1, 0, 'C')
        pdf.cell(45, 7, 'Salvo em', 1, 1, 'C')

        pdf.set_font('Helvetica', '', 8)
        for gp in group_predictions:
            pdf.cell(20, 6, f"Grupo {gp['group']}", 1, 0, 'C')
            pdf.cell(60, 6, remove_emojis(gp['first']), 1, 0, 'L')
            pdf.cell(60, 6, remove_emojis(gp['second']), 1, 0, 'L')
            pdf.cell(45, 6, gp['updated_at'], 1, 1, 'C')
    else:
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 7, "  Nenhum palpite de grupo registrado.", 0, 1)
    pdf.ln(5)

    # =========================================================================
    # SEÇÃO JOGOS
    # =========================================================================
    pdf.set_fill_color(255, 230, 200)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 9, '  PALPITES DE JOGOS', 1, 1, 'L', True)
    pdf.ln(2)

    if match_predictions:
        # Cabeçalho da tabela de jogos
        pdf.set_font('Helvetica', 'B', 7)
        pdf.cell(12, 7, 'Jogo', 1, 0, 'C')
        pdf.cell(30, 7, 'Data/Hora', 1, 0, 'C')
        pdf.cell(75, 7, 'Confronto e Palpite', 1, 0, 'C')
        pdf.cell(25, 7, 'Fase', 1, 0, 'C')
        pdf.cell(45, 7, 'Salvo em', 1, 1, 'C')

        pdf.set_font('Helvetica', '', 7)
        for mp in match_predictions:
            # Verifica se precisa de nova página
            if pdf.get_y() > 265:
                pdf.add_page()
                # Repete cabeçalho da tabela
                pdf.set_font('Helvetica', 'B', 7)
                pdf.cell(12, 7, 'Jogo', 1, 0, 'C')
                pdf.cell(30, 7, 'Data/Hora', 1, 0, 'C')
                pdf.cell(75, 7, 'Confronto e Palpite', 1, 0, 'C')
                pdf.cell(25, 7, 'Fase', 1, 0, 'C')
                pdf.cell(45, 7, 'Salvo em', 1, 1, 'C')
                pdf.set_font('Helvetica', '', 7)

            t1 = remove_emojis(mp['team1'])
            t2 = remove_emojis(mp['team2'])
            confronto = f"{t1} {mp['pred1']} x {mp['pred2']} {t2}"

            pdf.cell(12, 6, str(mp['number']), 1, 0, 'C')
            pdf.cell(30, 6, str(mp['match_time']), 1, 0, 'C')
            pdf.cell(75, 6, confronto, 1, 0, 'L')
            pdf.cell(25, 6, str(mp['phase']), 1, 0, 'C')
            pdf.cell(45, 6, str(mp['updated_at']), 1, 1, 'C')
    else:
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 7, "  Nenhum palpite de jogo registrado.", 0, 1)

    # Compatibilidade entre fpdf 1.7.2 (retorna str) e fpdf2 mais novo (retorna bytearray)
    output = pdf.output(dest='S')
    if isinstance(output, str):
        return output.encode('latin-1')
    elif isinstance(output, bytearray):
        return bytes(output)
    elif isinstance(output, bytes):
        return output
    return output.encode('latin-1') if hasattr(output, 'encode') else bytes(output)
