import os
import json
import sys
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def markdown_to_reportlab(text):
    """
    Very basic conversion of markdown-like syntax to ReportLab XML tags.
    Handles: **bold**, _italic_, and simple line breaks.
    Also handles custom @. indentation by stripping it (to be handled by Paragraph style).
    """
    if not isinstance(text, str):
        return str(text)
    
    # Handle bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Handle italic
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
    # Handle @. (custom notation used in JSON for list items)
    text = text.replace('@.', '')
    
    # Handle line breaks (ReportLab Paragraph uses <br/>)
    text = text.replace('\n', '<br/>')
    
    return text

def get_case_insensitive(d, key, default=None):
    if not isinstance(d, dict):
        return default
    for k, v in d.items():
        if k.lower() == key.lower():
            return v
    return default

class MOMReportLab:
    def __init__(self, json_path, output_pdf=None):
        self.json_path = json_path
        with open(json_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                self.data = data[0]
            else:
                self.data = data
        
        if not output_pdf:
            base = os.path.splitext(os.path.basename(json_path))[0]
            self.output_pdf = f"{base}_reportlab.pdf"
        else:
            self.output_pdf = output_pdf
            
        self.paragraph_count = 0
        self.styles = getSampleStyleSheet()
        self.setup_styles()

    def setup_styles(self):
        # Title Style
        self.styles.add(ParagraphStyle(
            name='MOM_Title',
            parent=self.styles['Heading1'],
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=10
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='MOM_Subtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=20
        ))

        # Agenda Heading
        self.styles.add(ParagraphStyle(
            name='MOM_AgendaHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            leading=14,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        ))

        # Normal text
        self.styles.add(ParagraphStyle(
            name='MOM_Normal',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12,
            spaceAfter=6,
            alignment=TA_LEFT
        ))
        
        # List indentation styles
        self.styles.add(ParagraphStyle(
            name='MOM_List1',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12,
            leftIndent=20,
            firstLineIndent=0,
            spaceAfter=4
        ))
        
        self.styles.add(ParagraphStyle(
            name='MOM_List2',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12,
            leftIndent=40,
            firstLineIndent=0,
            spaceAfter=4
        ))

    def create_pdf(self):
        doc = SimpleDocTemplate(
            self.output_pdf,
            pagesize=A4,
            rightMargin=25*mm,
            leftMargin=25*mm,
            topMargin=30*mm,
            bottomMargin=30*mm
        )
        
        story = []
        
        # Logo
        logo_path = 'logo.png'
        if os.path.exists(logo_path):
            img = Image(logo_path, width=160*mm, height=40*mm) # Adjust based on logo.png aspect ratio
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 10))

        # Header Info
        jenis = self.data.get("Jenis", "agm")
        if jenis == "exco":
            title_text = "MINIT MESYUARAT JAWATANKUASA EKSEKUTIF"
        else:
            title_text = "MINIT MESYUARAT AGUNG TAHUNAN"
            
        siri = self.data.get("Siri", "N/A")
        tarikh = self.data.get("Tarikh", "N/A")
        year_part = tarikh.split("/")[-1] if "/" in tarikh else "2025"
        tahun = year_part if len(year_part) == 4 else "20" + year_part
        
        story.append(Paragraph(title_text, self.styles['MOM_Title']))
        story.append(Paragraph(f"Siri {siri}/{tahun} pada {tarikh}", self.styles['MOM_Subtitle']))
        
        # Hadir
        story.append(Paragraph("HADIR", self.styles['MOM_AgendaHeader']))
        hadir = self.data.get('Hadir', {})
        story.extend(self.create_attendance_table(hadir))
        
        # Tidak Hadir
        tidak_hadir = get_case_insensitive(self.data, 'tidak hadir (dengan maaf)', {})
        if tidak_hadir:
            story.append(Paragraph("TIDAK HADIR (DENGAN MAAF)", self.styles['MOM_AgendaHeader']))
            story.extend(self.create_attendance_table(tidak_hadir))

        story.append(Spacer(1, 10))
        story.append(Table([['']], colWidths=[160*mm], style=[('LINEABOVE', (0,0), (-1,0), 1, colors.black)]))
        story.append(Spacer(1, 10))

        # Agenda
        agenda_items = self.parse_agenda()
        for i, item in enumerate(agenda_items, 1):
            perkara = get_case_insensitive(item, 'perkara', '').upper()
            story.append(Paragraph(f"AGENDA {i}: {perkara}", self.styles['MOM_AgendaHeader']))
            
            keterangan = get_case_insensitive(item, 'keterangan', '')
            self.process_text_blocks(keterangan, story, is_numbered=True)
            
            keputusan = get_case_insensitive(item, 'keputusan', '')
            if keputusan:
                # Decide if Keputusan gets a number. In many formats it doesn't, 
                # but if it's a main block of text it might. 
                # Keeping it simple for now and not numbering Keputusan prefix.
                story.append(Spacer(1, 4))
                story.append(Paragraph(f"<b>Keputusan:</b> {markdown_to_reportlab(keputusan)}", self.styles['MOM_Normal']))
            
            story.append(Spacer(1, 6))

        story.append(Spacer(1, 10))
        story.append(Table([['']], colWidths=[160*mm], style=[('LINEABOVE', (0,0), (-1,0), 1, colors.black)]))
        story.append(Spacer(1, 10))

        # Penutup
        story.append(Paragraph("PENUTUP", self.styles['MOM_AgendaHeader']))
        penutup = self.data.get('Penutup', '')
        self.process_text_blocks(penutup, story, is_numbered=True)

        story.append(Spacer(1, 20))

        # Signatories
        disediakan = get_case_insensitive(self.data, 'disediakan oleh', get_case_insensitive(self.data, 'disediakan', '....................'))
        diluluskan = get_case_insensitive(self.data, 'diluluskan oleh', get_case_insensitive(self.data, 'diluluskan', '....................'))
        
        sig_data = [
            [Paragraph(f"<b>Disediakan Oleh:</b><br/><br/><br/>{disediakan}", self.styles['MOM_Normal']),
             Paragraph(f"<b>Diluluskan Oleh:</b><br/><br/><br/>{diluluskan}", self.styles['MOM_Normal'])]
        ]
        sig_table = Table(sig_data, colWidths=[80*mm, 80*mm])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(sig_table)

        doc.build(story)
        return self.output_pdf

    def create_attendance_table(self, data_dict):
        story_part = []
        if isinstance(data_dict, str):
            story_part.append(Paragraph(markdown_to_reportlab(data_dict), self.styles['MOM_Normal']))
        elif isinstance(data_dict, dict):
            nama_list = get_case_insensitive(data_dict, 'nama', [])
            jawatan_list = get_case_insensitive(data_dict, 'jawatan', [])
            if nama_list:
                table_data = [['Name', 'Designation']]
                for i in range(len(nama_list)):
                    nama = nama_list[i] if i < len(nama_list) else ""
                    jawatan = jawatan_list[i] if i < len(jawatan_list) else ""
                    table_data.append([nama, jawatan])
                
                t = Table(table_data, colWidths=[100*mm, 60*mm])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                story_part.append(t)
            else:
                story_part.append(Paragraph("Tiada rekod berstruktur.", self.styles['MOM_Normal']))
        return story_part

    def parse_agenda(self):
        agenda_data = self.data.get('Agenda', {})
        agenda_items = []
        if isinstance(agenda_data, dict) and agenda_data:
            for key in sorted(agenda_data.keys(), key=lambda x: int(x) if x.isdigit() else 999):
                agenda_items.append(agenda_data[key])
        else:
            agenda_keys = sorted([k for k in self.data.keys() if k.startswith('Agenda_')], 
                                key=lambda x: int(x.split('_')[1]) if x.split('_')[1].isdigit() else 999)
            for k in agenda_keys:
                agenda_items.append(self.data[k])
        return agenda_items

    def process_text_blocks(self, text, story, is_numbered=False):
        if not text: return
        
        # Split by double newlines to handle blocks
        blocks = text.split('\n\n')
        for block in blocks:
            block = block.strip()
            if not block: continue
            
            # Check if it's a table (basic markdown table detection)
            if block.startswith('|'):
                story.append(self.md_table_to_reportlab(block))
                continue
            
            # Handle list items within the block
            lines = block.split('\n')
            for line in lines:
                line = line.strip()
                if not line: continue
                
                # Manual list patterns like a., b., (1), (2)
                is_level2 = re.match(r'^\([0-9]+\)', line)
                is_manual_list = re.match(r'^(\(?[a-z0-9]+\s*[.)]|\*|-|\+)', line, re.IGNORECASE)
                
                if is_level2:
                    style = self.styles['MOM_List2']
                elif is_manual_list:
                    style = self.styles['MOM_List1']
                else:
                    style = self.styles['MOM_Normal']
                    if is_numbered:
                        self.paragraph_count += 1
                        line = f"{self.paragraph_count}. {line}"
                
                story.append(Paragraph(markdown_to_reportlab(line), style))

    def md_table_to_reportlab(self, md_table):
        lines = [l.strip() for l in md_table.split('\n') if l.strip()]
        if len(lines) < 2: return Paragraph(markdown_to_reportlab(md_table), self.styles['MOM_Normal'])
        
        # Simple parsing for md table
        rows = []
        for line in lines:
            # skip table attributes or separator lines
            if line.startswith(':'): continue
            if re.match(r'^\|[\s:\-\|]*\|$', line): continue
            
            cells = [markdown_to_reportlab(c.strip()) for c in line.split('|')[1:-1]]
            if cells:
                rows.append([Paragraph(c, self.styles['MOM_Normal']) for c in cells])
        
        if not rows: return Spacer(1, 1)
        
        # Heuristic for column widths: if 3 columns, give more to the last one
        num_cols = len(rows[0])
        total_width = 160*mm
        if num_cols == 3:
            col_widths = [total_width * 0.2, total_width * 0.2, total_width * 0.6]
        elif num_cols == 2:
            col_widths = [total_width * 0.3, total_width * 0.7]
        else:
            col_widths = [total_width / num_cols] * num_cols
        
        t = Table(rows, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        return t

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_mom_reportlab.py <input_json>")
    else:
        mom = MOMReportLab(sys.argv[1])
        output = mom.create_pdf()
        print(f"Generated: {output}")
