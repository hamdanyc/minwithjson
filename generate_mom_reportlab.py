import os
import json
import sys
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

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
            self.data = json.load(f)
        
        if not output_pdf:
            base = os.path.splitext(os.path.basename(json_path))[0]
            self.output_pdf = f"{base}_reportlab.pdf"
        else:
            self.output_pdf = output_pdf
            
        self.styles = getSampleStyleSheet()
        self.setup_styles()

    def setup_styles(self):
        self.styles.add(ParagraphStyle(
            name='MOM_Title',
            parent=self.styles['Heading1'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=10
        ))
        self.styles.add(ParagraphStyle(
            name='MOM_Subtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='MOM_SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
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

    def create_pdf(self):
        doc = SimpleDocTemplate(
            self.output_pdf,
            pagesize=A4,
            rightMargin=25*mm,
            leftMargin=25*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        story = []
        header = self.data.get("Header", {})
        
        # Logo
        logo_path = 'logo.png'
        if os.path.exists(logo_path):
            img = Image(logo_path, width=160*mm, height=40*mm)
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 10))

        # Title/Subtitle
        jenis = header.get("Jenis", "agm")
        title_text = "MINIT MESYUARAT JAWATANKUASA EKSEKUTIF" if jenis == "exco" else "MINIT MESYUARAT AGUNG TAHUNAN"
        siri = header.get("Siri", "N/A")
        tarikh = header.get("Tarikh", "N/A")
        
        story.append(Paragraph(title_text, self.styles['MOM_Title']))
        story.append(Paragraph(f"Siri {siri} pada {tarikh}", self.styles['MOM_Subtitle']))
        
        # Attendance
        attn = self.data.get("Attendance", {})
        story.append(Paragraph("HADIR", self.styles['MOM_SectionHeader']))
        story.append(self.create_attendance_table(attn.get("Hadir", [])))
        
        tidak_hadir = attn.get("Tidak Hadir", [])
        if tidak_hadir:
            story.append(Paragraph("TIDAK HADIR (DENGAN MAAF)", self.styles['MOM_SectionHeader']))
            story.append(self.create_attendance_table(tidak_hadir, includes_excuse=True))

        story.append(Spacer(1, 10))
        
        # Chairman Address
        if self.data.get("ChairmanAddress"):
            story.append(Paragraph("1. UCAPAN ALU-ALUAN PENGERUSI", self.styles['MOM_SectionHeader']))
            story.append(Paragraph(markdown_to_reportlab(self.data["ChairmanAddress"]), self.styles['MOM_Normal']))

        # Approval of Minutes
        if self.data.get("ApprovalOfPrevMinutes"):
            story.append(Paragraph("2. PENGESAHAN MINIT MESYUARAT YANG LALU", self.styles['MOM_SectionHeader']))
            story.append(Paragraph(markdown_to_reportlab(self.data["ApprovalOfPrevMinutes"]), self.styles['MOM_Normal']))

        # Matters Arising
        ma = self.data.get("MattersArising", [])
        if ma:
            story.append(Paragraph("3. PERKARA-PERKARA BERBANGKIT", self.styles['MOM_SectionHeader']))
            table_data = [['Perkara', 'Status', 'Tindakan/Maklumbalas']]
            for item in ma:
                table_data.append([
                    Paragraph(markdown_to_reportlab(item.get("item", "")), self.styles['MOM_Normal']),
                    item.get("status", ""),
                    Paragraph(markdown_to_reportlab(item.get("outcome", "")), self.styles['MOM_Normal'])
                ])
            t = Table(table_data, colWidths=[60*mm, 30*mm, 70*mm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(t)

        # Reports
        reports = self.data.get("Reports", {})
        if reports.get("Financial"):
            story.append(Paragraph("4. LAPORAN KEWANGAN", self.styles['MOM_SectionHeader']))
            story.append(Paragraph(markdown_to_reportlab(reports["Financial"]), self.styles['MOM_Normal']))
        if reports.get("Membership"):
            story.append(Paragraph("5. LAPORAN KEAHLIAN", self.styles['MOM_SectionHeader']))
            story.append(Paragraph(markdown_to_reportlab(reports["Membership"]), self.styles['MOM_Normal']))

        # New Matters
        nm = self.data.get("NewMatters", [])
        if nm:
            story.append(Paragraph("6. HAL-HAL LAIN", self.styles['MOM_SectionHeader']))
            for i, item in enumerate(nm, 1):
                story.append(Paragraph(f"6.{i} {markdown_to_reportlab(item.get('item', ''))}", self.styles['MOM_Normal']))
                if item.get("keputusan"):
                    story.append(Paragraph(f"<b>Keputusan:</b> {markdown_to_reportlab(item['keputusan'])}", self.styles['MOM_Normal']))

        # Closing
        if self.data.get("Closing"):
            story.append(Paragraph("PENUTUP", self.styles['MOM_SectionHeader']))
            story.append(Paragraph(markdown_to_reportlab(self.data["Closing"]), self.styles['MOM_Normal']))

        doc.build(story)
        return self.output_pdf

    def create_attendance_table(self, attendance_list, includes_excuse=False):
        if not attendance_list:
            return Paragraph("Tiada rekod.", self.styles['MOM_Normal'])
        
        headers = ['Nama', 'Jawatan']
        col_widths = [100*mm, 60*mm]
        if includes_excuse:
            headers.append('Sebab')
            col_widths = [70*mm, 45*mm, 45*mm]
            
        table_data = [headers]
        for person in attendance_list:
            row = [person.get("nama", ""), person.get("jawatan", "")]
            if includes_excuse:
                row.append(person.get("sebab", ""))
            table_data.append(row)
            
        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        return t

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mom = MOMReportLab(sys.argv[1])
        mom.create_pdf()
