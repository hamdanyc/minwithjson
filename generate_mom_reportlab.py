import os
import json
import sys
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

def markdown_to_reportlab(text):
    if not isinstance(text, str):
        return str(text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
    text = text.replace('\n', '<br/>')
    return text

class MOMReportLab:
    def __init__(self, json_path, output_pdf=None):
        self.json_path = json_path
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        # Handle list-wrapped JSON
        if isinstance(json_data, list) and len(json_data) > 0:
            self.data = json_data[0]
        else:
            self.data = json_data
        
        if not output_pdf:
            base = os.path.splitext(os.path.basename(json_path))[0]
            self.output_pdf = f"{base}_reportlab.pdf"
        else:
            self.output_pdf = output_pdf
            
        self.styles = getSampleStyleSheet()
        self.setup_styles()
        self.paragraph_counter = 0

    def setup_styles(self):
        self.styles.add(ParagraphStyle(
            name='MOM_HeaderBlock',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='MOM_SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=11,
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='MOM_Normal',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))
        self.styles.add(ParagraphStyle(
            name='MOM_AnnexHeader',
            parent=self.styles['Heading1'],
            fontSize=12,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceBefore=20,
            spaceAfter=15
        ))
        self.styles.add(ParagraphStyle(
            name='MOM_TableText',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=11
        ))
        self.styles.add(ParagraphStyle(
            name='MOM_Indented',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12,
            spaceAfter=6,
            leftIndent=24, # Increased indentation to align with text after number
            alignment=TA_JUSTIFY
        ))

    def get_next_num(self):
        self.paragraph_counter += 1
        return self.paragraph_counter

    def parse_markdown_table(self, text):
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        table_data = []
        
        for line in lines:
            if line.startswith('|') and line.endswith('|'):
                if set(line.replace('|', '').replace('-', '').replace(' ', '')) <= {':'}:
                    continue
                cells = [c.strip() for c in line.split('|')[1:-1]]
                table_data.append([Paragraph(markdown_to_reportlab(c), self.styles['MOM_TableText']) for c in cells])
        
        return table_data

    def create_pdf(self):
        def add_page_number(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 10)
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(A4[0]/2, 10*mm, f"{page_num}")
            canvas.restoreState()

        doc = SimpleDocTemplate(
            self.output_pdf,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        story = []
        header = self.data.get("Header", {})
        
        # Logo
        logo_path = 'logo.png'
        if os.path.exists(logo_path):
            img = Image(logo_path)
            # Maintain aspect ratio and set to a reasonable width
            orig_w, orig_h = img.imageWidth, img.imageHeight
            aspect = orig_h / orig_w
            
            target_width = 160*mm 
            img.drawWidth = target_width
            img.drawHeight = target_width * aspect
            
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 5))

        # Header Block
        header = self.data.get("Header", self.data) # Fallback to top level for legacy
        jenis = str(header.get("Jenis", header.get("jenis", "exco"))).upper()
        title_type = "JAWATANKUASA EKSEKUTIF" if jenis == "EXCO" else "AGUNG TAHUNAN"
        siri = header.get("Siri", header.get("siri", "N/A"))
        tarikh = str(header.get("Tarikh", header.get("tarikh", "N/A"))).upper()
        masa = str(header.get("Masa", header.get("masa", "N/A"))).upper()
        tempat = str(header.get("Tempat", header.get("tempat", "N/A"))).upper()
        
        header_text = f"MINIT MESYUARAT {title_type} SIRI {siri}<br/>PADA {tarikh} JAM {masa}<br/>DI {tempat}"
        story.append(Paragraph(header_text, self.styles['MOM_HeaderBlock']))
        story.append(Spacer(1, 15))
        
        # Attendance
        attn = self.data.get("Attendance", {})
        hadir_data = attn.get("Hadir", self.data.get("Hadir", []))
        story.append(Paragraph("HADIR", self.styles['MOM_SectionHeader']))
        story.append(self.create_attendance_table(hadir_data))
        
        tidak_hadir_data = attn.get("Tidak Hadir", self.data.get("Tidak_hadir", []))
        if tidak_hadir_data:
            story.append(Spacer(1, 5))
            story.append(Paragraph("TIDAK HADIR (DENGAN MAAF)", self.styles['MOM_SectionHeader']))
            story.append(self.create_attendance_table(tidak_hadir_data, includes_excuse=True))

        story.append(Spacer(1, 10))
        
        # Main Content
        # We handle both modern schema and legacy Agenda_X schema
        
        # 1. Chairman Address / Agenda 1
        agenda1_data = self.data.get("ChairmanAddress", {})
        if isinstance(agenda1_data, str):
            chairman_address = agenda1_data
            title = "UCAPAN PEMBUKAAN OLEH PRESIDEN"
        else:
            chairman_address = agenda1_data.get("Keterangan", "")
            title = agenda1_data.get("Perkara", "UCAPAN PEMBUKAAN OLEH PRESIDEN")
            
        if chairman_address:
            story.append(PageBreak()) # Force Agenda 1 to start on a new page (Page 2)
            
            # Use KeepTogether to ensure title and content stay on the same page
            agenda1_flowables = []
            agenda1_flowables.append(Paragraph(f"AGENDA 1: {title}", self.styles['MOM_SectionHeader']))
            self.add_numbered_paragraphs(agenda1_flowables, chairman_address)
            agenda1_flowables.append(Paragraph(f"{self.get_next_num()}. Keputusan. Makluman.", self.styles['MOM_Normal']))
            
            story.append(KeepTogether(agenda1_flowables))

        # 2. Approval of Minutes / Agenda 2
        agenda2_data = self.data.get("ApprovalOfPrevMinutes", {})
        if isinstance(agenda2_data, str):
            approval = agenda2_data
            title = f"MENGESAHKAN MINIT MESYUARAT JAWATANKUASA SIRI {header.get('Siri', 'LALU')}"
        else:
            approval = agenda2_data.get("Keterangan", "")
            title = agenda2_data.get("Perkara", f"MENGESAHKAN MINIT MESYUARAT JAWATANKUASA SIRI {header.get('Siri', 'LALU')}")
            
        if approval:
            story.append(Paragraph(f"AGENDA 2: {title}", self.styles['MOM_SectionHeader']))
            self.add_numbered_paragraphs(story, approval)
            story.append(Paragraph(f"{self.get_next_num()}. Keputusan. Makluman.", self.styles['MOM_Normal']))

        # 3. Matters Arising / Agenda 3
        agenda3 = self.data.get("Agenda_3", {}) # Legacy support
        ma = self.data.get("MattersArising", [])
        
        title = agenda3.get("Perkara", "PERKARA-PERKARA BERBANGKIT")
        story.append(Paragraph(f"AGENDA 3: {title}", self.styles['MOM_SectionHeader']))
        
        if ma:
            for item in ma:
                num = self.get_next_num()
                perkara = item.get("Perkara", "")
                keterangan = item.get("Keterangan", "")
                keputusan = item.get("Keputusan", "")

                # Unified rendering for multi-paragraph and sub-lists
                if keterangan.strip().startswith('|'):
                     prefix = f"<b>{num}. {perkara}</b>.\n"
                else:
                     prefix = f"<b>{num}. {perkara}</b>. " if perkara else f"<b>{num}. </b>"
                
                self.render_numbered_content(story, keterangan, first_prefix=prefix)
                
                # Display Keputusan as a numbered paragraph
                if keputusan:
                    story.append(Paragraph(f"{self.get_next_num()}. Keputusan: {keputusan}", self.styles['MOM_Normal']))
        elif agenda3 and agenda3.get("Keterangan"):
            self.add_numbered_paragraphs(story, agenda3.get("Keterangan", ""))
        else:
            story.append(Paragraph(f"{self.get_next_num()}. Tiada", self.styles['MOM_Normal']))


        # 4. Financial Report / Agenda 4
        rep_data = self.data.get("Reports", {})
        fin_data = rep_data.get("Financial", {})
        if isinstance(fin_data, str):
            financial = fin_data
            title = "LAPORAN KEWANGAN BERAKHIR"
        else:
            financial = fin_data.get("Keterangan", "")
            title = fin_data.get("Perkara", "LAPORAN KEWANGAN BERAKHIR")
            
        if financial:
            story.append(Paragraph(f"AGENDA 4: {title}", self.styles['MOM_SectionHeader']))
            self.add_numbered_paragraphs(story, financial)
            story.append(Paragraph(f"{self.get_next_num()}. Keputusan. Makluman.", self.styles['MOM_Normal']))
            
        # 5. Membership Report / Agenda 5
        mem_data = rep_data.get("Membership", {})
        if isinstance(mem_data, str):
            membership = mem_data
            title = "LAPORAN KEAHLIAN BERAKHIR"
        else:
            membership = mem_data.get("Keterangan", "")
            title = mem_data.get("Perkara", "LAPORAN KEAHLIAN BERAKHIR")
            
        if membership:
            story.append(Paragraph(f"AGENDA 5: {title}", self.styles['MOM_SectionHeader']))
            self.add_numbered_paragraphs(story, membership)
            story.append(Paragraph(f"{self.get_next_num()}. Keputusan. Makluman.", self.styles['MOM_Normal']))

        # 6. New Matters / Agenda 6
        agenda6 = self.data.get("Agenda_6", {}) # Legacy
        nm_raw = self.data.get("NewMatters", [])
        
        # Filter out empty or placeholder rows
        nm = []
        for item in nm_raw:
            perkara = str(item.get("Perkara", "")).strip()
            keterangan = str(item.get("Keterangan", "")).strip()
            keputusan = str(item.get("Keputusan", "")).strip()
            
            # If all fields are empty or just "Tiada", it's considered empty
            is_empty = not (perkara or keterangan or keputusan)
            is_placeholder = all(val.lower() in ["tiada", "", "none"] for val in [perkara, keterangan, keputusan])
            
            if not (is_empty or is_placeholder):
                nm.append(item)

        if nm or (agenda6 and agenda6.get("Keterangan")):
            title = agenda6.get("Perkara", "PERKARA-PERKARA BAHARU DARIPADA AHLI JAWATANKUASA")
            story.append(Paragraph(f"AGENDA 6: {title}", self.styles['MOM_SectionHeader']))
            if nm:
                for item in nm:
                    num = self.get_next_num()
                    perkara = item.get("Perkara", "")
                    keterangan = item.get("Keterangan", "")
                    keputusan = item.get("Keputusan", "")
                    

                    # Unified rendering for multi-paragraph and sub-lists
                    if keterangan.strip().startswith('|'):
                        prefix = f"<b>{num}. {perkara}</b>.\n"
                    else:
                        prefix = f"<b>{num}. {perkara}</b>. " if perkara else f"<b>{num}. </b>"
                    
                    self.render_numbered_content(story, keterangan, first_prefix=prefix)
                    
                    if keputusan:
                        story.append(Paragraph(f"{self.get_next_num()}. Keputusan: {markdown_to_reportlab(keputusan)}", self.styles['MOM_Normal']))
            elif agenda6:
                self.add_numbered_paragraphs(story, agenda6.get("Keterangan", ""))

        # Closing
        closing = self.data.get("Closing", self.data.get("Penutup", ""))
        if closing:
            story.append(Paragraph("PENUTUP", self.styles['MOM_SectionHeader']))
            self.add_numbered_paragraphs(story, closing)

        # Signature Sections
        story.append(Spacer(1, 20))
        
        # Prepare signature images
        prep_sig_path = 'Kol_Hamdan.png'
        appr_sig_path = 'dsaa_sign.png'
        
        def get_sig_img(path):
            if os.path.exists(path):
                img = Image(path, width=40*mm, height=20*mm)
                img.hAlign = 'LEFT'
                return img
            return Spacer(1, 20*mm)

        sig_data = [
            [Paragraph("<b>Disediakan Oleh:</b>", self.styles['MOM_Normal']), 
             Paragraph("<b>Diluluskan Oleh:</b>", self.styles['MOM_Normal'])],
            [get_sig_img(prep_sig_path), get_sig_img(appr_sig_path)],
            [Paragraph("Mej Tengku Ahmad Nazri bin Tengku Abdul Jalil (B)", self.styles['MOM_Normal']),
             Paragraph("Lt Jen Dato' Sri Abdul Aziz bin Ibrahim (B)", self.styles['MOM_Normal'])]
        ]
        
        sig_table = Table(sig_data, colWidths=[80*mm, 80*mm])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(KeepTogether(sig_table))

        # Annex (Kembaran)
        annex_content = self.data.get("Annex", "")
        if annex_content:
            story.append(PageBreak())
            story.append(Paragraph("KEMBARAN-KEMBARAN:", self.styles['MOM_AnnexHeader']))
            
            lines = annex_content.split('\n')
            current_table = []
            
            for line in lines:
                if line.strip().startswith('|'):
                    current_table.append(line)
                else:
                    if current_table:
                        self.flush_annex_table(story, current_table)
                        current_table = []
                    
                    if line.strip():
                        story.append(Paragraph(markdown_to_reportlab(line), self.styles['MOM_Normal']))
            
            if current_table:
                self.flush_annex_table(story, current_table)

        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        return self.output_pdf

    def add_numbered_paragraphs(self, story, content):
        self.render_numbered_content(story, content)

    def render_numbered_content(self, story, content, first_prefix=None):
        if not content:
            if first_prefix:
                self.add_content_with_tables(story, first_prefix)
            return
            
        parts = re.split(r'@\.\s*', content)
        parts = [p.strip() for p in parts if p.strip()]
        
        if not parts and first_prefix:
             self.add_content_with_tables(story, first_prefix)
             return

        for idx, part in enumerate(parts):
            # Split for sub-lists (a., b., c.)
            sub_parts = re.split(r'(?:\n|^)\s*([a-z]\.)\s+', part)
            lead_in = sub_parts[0]
            
            if idx == 0 and first_prefix:
                # Use provided prefix for the first paragraph
                self.add_content_with_tables(story, f"{first_prefix}{lead_in}")
            else:
                # Use a new number for subsequent paragraphs
                num = self.get_next_num()
                self.add_content_with_tables(story, f"{num}. {lead_in}")
            
            # Render sub-items if present
            for i in range(1, len(sub_parts), 2):
                marker = sub_parts[i]
                text = sub_parts[i+1]
                # Indent sub-items
                self.add_content_with_tables(story, f"&nbsp;&nbsp;&nbsp;&nbsp;{marker} {text}")

    def add_content_with_tables(self, story, text, style_name='MOM_Normal'):
        lines = text.split('\n')
        current_table = []
        for line in lines:
            if line.strip().startswith('|'):
                current_table.append(line)
            else:
                if current_table:
                    self.flush_annex_table(story, current_table)
                    current_table = []
                if line.strip():
                    story.append(Paragraph(markdown_to_reportlab(line), self.styles[style_name]))
        if current_table:
            self.flush_annex_table(story, current_table)

    def flush_annex_table(self, story, current_table):
        # We need raw text to calculate lengths before wrapping in Paragraphs
        raw_table_data = []
        lines = [line.strip() for line in '\n'.join(current_table).split('\n') if line.strip()]
        for line in lines:
            if line.startswith('|') and line.endswith('|'):
                if set(line.replace('|', '').replace('-', '').replace(' ', '')) <= {':'}:
                    continue
                cells = [c.strip() for c in line.split('|')[1:-1]]
                raw_table_data.append(cells)
        
        if not raw_table_data:
            return

        num_cols = len(raw_table_data[0])
        available_width = A4[0] - 40*mm
        
        # Calculate max length in each column
        max_lengths = [0] * num_cols
        for row in raw_table_data:
            for i, cell in enumerate(row):
                if i < num_cols:
                    max_lengths[i] = max(max_lengths[i], len(cell))
        
        total_len = sum(max_lengths) or 1
        
        # Proportional width calculation with a minimum of 10% each if too many cols
        col_widths = []
        for length in max_lengths:
            width = (length / total_len) * available_width
            # Ensure a sensible minimum (e.g., 20mm or 10% of available)
            min_w = max(20*mm, available_width * 0.1)
            col_widths.append(max(width, min_w))
            
        # Re-distribute if we exceed available_width
        current_total = sum(col_widths)
        if current_total > available_width:
            ratio = available_width / current_total
            col_widths = [w * ratio for w in col_widths]

        # Convert raw data to Paragraph objects for the table
        table_data = []
        for row in raw_table_data:
            table_data.append([Paragraph(markdown_to_reportlab(c), self.styles['MOM_TableText']) for c in row])

        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
        ]))
        story.append(t)

    def create_attendance_table(self, attendance_list, includes_excuse=False):
        if not attendance_list:
            return Paragraph("Tiada rekod.", self.styles['MOM_Normal'])
        
        # Handle legacy structure: {"Nama": ["Name 1", "Name 2"]}
        if isinstance(attendance_list, dict) and "Nama" in attendance_list:
            names = attendance_list["Nama"]
            # Convert to list of dicts
            attendance_list = [{"nama": n} for n in names]
        
        # Handle simple list of strings (if not legacy dict structure)
        if isinstance(attendance_list, list) and len(attendance_list) > 0 and isinstance(attendance_list[0], str):
            attendance_list = [{"nama": n} for n in attendance_list]

        # Table headers matching example: Nama, Singkatan, Jawatan
        headers = ['Nama', 'Singkatan', 'Jawatan']
        col_widths = [80*mm, 30*mm, 50*mm]
        
        if includes_excuse:
            headers = ['Nama', 'Singkatan', 'Jawatan', 'Sebab']
            col_widths = [65*mm, 25*mm, 35*mm, 35*mm]
            
        table_data = [[Paragraph(f"<b>{h}</b>", self.styles['MOM_TableText']) for h in headers]]
        for person in attendance_list:
            if isinstance(person, str):
                person = {"nama": person}
            row = [
                Paragraph(person.get("nama", ""), self.styles['MOM_TableText']),
                Paragraph(person.get("singkatan", ""), self.styles['MOM_TableText']),
                Paragraph(person.get("jawatan", ""), self.styles['MOM_TableText'])
            ]
            if includes_excuse:
                row.append(Paragraph(person.get("sebab", ""), self.styles['MOM_TableText']))
            table_data.append(row)
            
        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            # Borderless as per example
        ]))
        return t

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mom = MOMReportLab(sys.argv[1])
        mom.create_pdf()
