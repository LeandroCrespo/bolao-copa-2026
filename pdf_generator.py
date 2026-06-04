
import os
from fpdf import FPDF
from datetime import datetime
import pytz

def get_brazil_time_str(dt):
    if not dt:
        return "N/A"
    # Assume que o dt do banco está em UTC
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    br_tz = pytz.timezone('America/Sao_Paulo')
    dt_br = dt.astimezone(br_tz)
    return dt_br.strftime("%d/%m/%Y %H:%M:%S")

class PredictionPDF(FPDF):
    def header(self):
        # Logo (se existir)
        # self.image('assets/logo_copa2026.png', 10, 8, 33)
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'Comprovante de Palpites - Bolão Copa 2026', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()} | Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', 0, 0, 'C')

def generate_user_backup_pdf(user_name, match_predictions, group_predictions, podium_prediction):
    pdf = PredictionPDF()
    pdf.add_page()
    
    # Informações do Usuário
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'Participante: {user_name}', 0, 1)
    pdf.ln(5)
    
    # --- SEÇÃO PÓDIO ---
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '🏆 PALPITE DE PÓDIO', 1, 1, 'L', 1)
    pdf.set_font('Arial', '', 10)
    
    if podium_prediction:
        pdf.cell(0, 8, f"Campeão: {podium_prediction['champion']}", 0, 1)
        pdf.cell(0, 8, f"Vice-Campeão: {podium_prediction['runner_up']}", 0, 1)
        pdf.cell(0, 8, f"3º Lugar: {podium_prediction['third_place']}", 0, 1)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 8, f"Salvo em: {podium_prediction['updated_at']}", 0, 1)
    else:
        pdf.cell(0, 8, "Nenhum palpite de pódio registrado.", 0, 1)
    pdf.ln(5)
    
    # --- SEÇÃO GRUPOS ---
    pdf.set_fill_color(200, 255, 220)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '🏅 PALPITES DE GRUPOS (1º e 2º Colocados)', 1, 1, 'L', 1)
    pdf.set_font('Arial', '', 9)
    
    # Tabela de Grupos
    pdf.cell(30, 8, 'Grupo', 1, 0, 'C')
    pdf.cell(60, 8, '1º Colocado', 1, 0, 'C')
    pdf.cell(60, 8, '2º Colocado', 1, 0, 'C')
    pdf.cell(40, 8, 'Salvo em', 1, 1, 'C')
    
    for gp in group_predictions:
        pdf.cell(30, 7, f"Grupo {gp['group']}", 1, 0, 'C')
        pdf.cell(60, 7, gp['first'], 1, 0, 'L')
        pdf.cell(60, 7, gp['second'], 1, 0, 'L')
        pdf.cell(40, 7, gp['updated_at'], 1, 1, 'C')
    pdf.ln(5)
    
    # --- SEÇÃO JOGOS ---
    pdf.set_fill_color(255, 230, 200)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '🏟️ PALPITES DE JOGOS', 1, 1, 'L', 1)
    pdf.ln(2)
    
    # Cabeçalho da tabela de jogos
    pdf.set_font('Arial', 'B', 8)
    pdf.cell(15, 7, 'Jogo', 1, 0, 'C')
    pdf.cell(35, 7, 'Data/Hora Jogo', 1, 0, 'C')
    pdf.cell(70, 7, 'Confronto e Palpite', 1, 0, 'C')
    pdf.cell(30, 7, 'Fase', 1, 0, 'C')
    pdf.cell(40, 7, 'Salvo em', 1, 1, 'C')
    
    pdf.set_font('Arial', '', 8)
    for mp in match_predictions:
        # Verifica se precisa de nova página
        if pdf.get_y() > 260:
            pdf.add_page()
            # Repete cabeçalho da tabela
            pdf.set_font('Arial', 'B', 8)
            pdf.cell(15, 7, 'Jogo', 1, 0, 'C')
            pdf.cell(35, 7, 'Data/Hora Jogo', 1, 0, 'C')
            pdf.cell(70, 7, 'Confronto e Palpite', 1, 0, 'C')
            pdf.cell(30, 7, 'Fase', 1, 0, 'C')
            pdf.cell(40, 7, 'Salvo em', 1, 1, 'C')
            pdf.set_font('Arial', '', 8)
            
        confronto = f"{mp['team1']} {mp['pred1']} x {mp['pred2']} {mp['team2']}"
        pdf.cell(15, 6, str(mp['number']), 1, 0, 'C')
        pdf.cell(35, 6, mp['match_time'], 1, 0, 'C')
        pdf.cell(70, 6, confronto, 1, 0, 'L')
        pdf.cell(30, 6, mp['phase'], 1, 0, 'C')
        pdf.cell(40, 6, mp['updated_at'], 1, 1, 'C')
        
    return pdf.output(dest='S')
