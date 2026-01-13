import json
import os
import re

def initialize_mom_state():
    """Returns a default structure for a new MOM."""
    return {
        "Header": {
            "Title": "",
            "Siri": "",
            "Tarikh": "",
            "Masa": "",
            "Tempat": "",
            "Jenis": "agm" # or 'exco'
        },
        "Attendance": {
            "Hadir": [],
            "Tidak Hadir": []
        },
        "ChairmanAddress": {
            "Perkara": "UCAPAN PEMBUKAAN OLEH PRESIDEN",
            "Keterangan": ""
        },
        "ApprovalOfPrevMinutes": {
            "Perkara": "MENGESAHKAN MINIT MESYUARAT JAWATANKUASA SIRI 3/2024 PADA 23 JUN 2024",
            "Keterangan": "Timbalan Presiden mencadangkan minit diluluskan dan disokong oleh Naib Presiden (Udara)."
        },
        "MattersArising": [], # List of {Perkara, Keputusan, Keterangan}
        "Reports": {
            "Financial": {
                "Perkara": "LAPORAN KEWANGAN BERAKHIR",
                "Keterangan": "Laporan oleh BK"
            },
            "Membership": {
                "Perkara": "LAPORAN KEAHLIAN BERAKHIR",
                "Keterangan": "Laporan oleh JK Keahlian"
            }
        },
        "NewMatters": [], # List of {Perkara, Keputusan, Keterangan}
        "Closing": "",
        "Annex": ""
    }

def ingest_previous_mom(json_data):
    """
    Parses a previous MOM JSON and extracts items for the next meeting.
    1. Carry over Header (increment Siri)
    2. Transfrom NewMatters -> MattersArising
    3. Load Attendance (Hadir/Tidak Hadir)
    4. Support Legacy Agenda/Agenda_X structure
    """
    # Handle list-wrapped JSON (e.g., [ {...} ])
    if isinstance(json_data, list):
        if len(json_data) > 0 and isinstance(json_data[0], dict):
            json_data = json_data[0]
        else:
            return initialize_mom_state()

    new_state = initialize_mom_state()
    
    # Helper for case-insensitive and loose key matching
    def find_key(data, pattern):
        pattern = pattern.lower().replace("_", " ").replace("-", " ")
        for k in data.keys():
            k_norm = k.lower().replace("_", " ").replace("-", " ")
            if pattern in k_norm:
                return k
        return None

    # Carry over basic info
    header_key = find_key(json_data, "Header")
    # Load Header info
    header = json_data.get("Header", json_data)
    new_state["Header"]["Title"] = header.get("Title", header.get("title", ""))
    siri = header.get("Siri", header.get("siri", ""))
    if "/" in siri:
        try:
            num, year = siri.split("/")
            new_state["Header"]["Siri"] = f"{int(num)+1}/{year}"
        except:
            new_state["Header"]["Siri"] = siri
    else:
        new_state["Header"]["Siri"] = siri
    new_state["Header"]["Tarikh"] = header.get("Tarikh", header.get("tarikh", ""))
    new_state["Header"]["Masa"] = header.get("Masa", header.get("masa", ""))
    new_state["Header"]["Tempat"] = header.get("Tempat", header.get("tempat", ""))
    new_state["Header"]["Jenis"] = header.get("Jenis", header.get("jenis", "agm"))

    # Mapping for Agenda items in previous JSON to current state
    agenda1 = json_data.get("Agenda_1", {})
    # Handle legacy string or new dict
    ca_prev = json_data.get("ChairmanAddress", {})
    new_state["ChairmanAddress"]["Keterangan"] = ca_prev.get("Keterangan", agenda1.get("Keterangan", "")) if isinstance(ca_prev, dict) else ca_prev
    
    agenda2 = json_data.get("Agenda_2", {})
    ap_prev = json_data.get("ApprovalOfPrevMinutes", {})
    new_state["ApprovalOfPrevMinutes"]["Keterangan"] = ap_prev.get("Keterangan", agenda2.get("Keterangan", "")) if isinstance(ap_prev, dict) else ap_prev
    
    reports = json_data.get("Reports", {})
    agenda4 = json_data.get("Agenda_4", {})
    agenda5 = json_data.get("Agenda_5", {})
    
    fin_prev = reports.get("Financial", {})
    new_state["Reports"]["Financial"]["Keterangan"] = fin_prev.get("Keterangan", agenda5.get("Keterangan", "")) if isinstance(fin_prev, dict) else fin_prev
    
    mem_prev = reports.get("Membership", {})
    new_state["Reports"]["Membership"]["Keterangan"] = mem_prev.get("Keterangan", agenda4.get("Keterangan", "")) if isinstance(mem_prev, dict) else mem_prev

    # Ingest Attendance
    def parse_attendance(attn_data):
        if not isinstance(attn_data, dict):
            return []
        
        # Support both { nama: [], jawatan: [] } and [ { nama, jawatan } ]
        names = attn_data.get("Nama", attn_data.get("nama", []))
        if isinstance(names, list) and names and not isinstance(names[0], dict):
            # Column-based structure
            jawatan = attn_data.get("Jawatan", attn_data.get("jawatan", []))
            singkatan = attn_data.get("Singkatan", attn_data.get("singkatan", []))
            records = []
            for i in range(len(names)):
                records.append({
                    "siri": str(i+1),
                    "nama": names[i],
                    "jawatan": jawatan[i] if i < len(jawatan) else "",
                    "singkatan": singkatan[i] if i < len(singkatan) else ""
                })
            return records
        elif isinstance(names, list) and names and isinstance(names[0], dict):
            # List of dicts structure
            records = []
            for i, d in enumerate(names):
                records.append({
                    "siri": d.get("siri", str(i+1)),
                    "nama": d.get("nama", ""),
                    "jawatan": d.get("jawatan", ""),
                    "singkatan": d.get("singkatan", "")
                })
            return records
        return []

    # Handle various Hadir/Tidak Hadir keys
    hadir_key = find_key(json_data, "Hadir")
    if hadir_key:
        new_state["Attendance"]["Hadir"] = parse_attendance(json_data[hadir_key])
    
    # Check for "Tidak hadir" variants
    tidak_key = find_key(json_data, "Tidak hadir")
    if tidak_key:
        new_state["Attendance"]["Tidak Hadir"] = parse_attendance(json_data[tidak_key])

    # Transform Previous 'NewMatters' into 'MattersArising' (New Schema)
    nm_key = find_key(json_data, "NewMatters")
    if nm_key:
        for item in json_data[nm_key]:
            new_state["MattersArising"].append({
                "Perkara": item.get("Perkara", item.get("item", "")),
                "Keputusan": "Pelaksanaan",
                "Keterangan": item.get("Keterangan", item.get("keputusan", ""))
            })
            
    # Also carry over any unresolved 'MattersArising' from the previous meeting (New Schema)
    ma_key = find_key(json_data, "MattersArising")
    if ma_key:
        for item in json_data[ma_key]:
            status = item.get("status", item.get("Keputusan", "Pelaksanaan"))
            if status != "Selesai":
                new_state["MattersArising"].append({
                    "Perkara": item.get("item", item.get("Perkara", "")),
                    "Keputusan": status,
                    "Keterangan": item.get("outcome", item.get("Keterangan", ""))
                })

    # --- Legacy Schema Support ---
    if not new_state["MattersArising"]:
        agenda_items = []
        # Check for single "Agenda" dictionary
        if "Agenda" in json_data and isinstance(json_data["Agenda"], dict):
            keys = sorted(json_data["Agenda"].keys(), key=lambda x: int(x) if x.isdigit() else 999)
            for k in keys:
                agenda_items.append(json_data["Agenda"][k])
        
        # Check for multiple "Agenda_X" keys
        agenda_keys = sorted([k for k in json_data.keys() if k.startswith("Agenda_")], 
                            key=lambda x: int(x.split("_")[1]) if x.split("_")[1].isdigit() else 999)
        for ak in agenda_keys:
            if isinstance(json_data[ak], dict):
                item = json_data[ak]
                # Store the original key to identify Agenda_3 and Agenda_6
                item["_source_key"] = ak
                agenda_items.append(item)

        for item in agenda_items:
            # Normalize content function
            def normalize_content(c):
                if isinstance(c, list):
                    # Join list elements, keeping "@." if present to allow PDF generator to number them
                    return "\n".join([str(x).strip() for x in c])
                return str(c)

            perkara = normalize_content(item.get("Perkara", item.get("perkara", "")))
            keputusan = normalize_content(item.get("Keputusan", item.get("keputusan", "")))
            keterangan = normalize_content(item.get("Keterangan", item.get("keterangan", "")))
            
            # If it's a non-information decision, it's a follow-up
            info_keywords = ["makluman", "maklum", "noted", "information"]
            is_info = any(kw in keputusan.lower() for kw in info_keywords)
            
            source_key = item.get("_source_key", "")
            # Explicitly include items from Agenda_3 (Berbangkit) and Agenda_6 (Baharu)
            # as per user request, regardless of "makluman" status
            is_priority_section = "Agenda_3" in source_key or "Agenda_6" in source_key

            if ((keputusan and not is_info) or is_priority_section) and not is_priority_section:
                desc = f"{perkara}: {keputusan}" if keputusan else perkara
                new_state["MattersArising"].append({
                    "Perkara": desc,
                    "Keputusan": "Pelaksanaan",
                    "Keterangan": keterangan # Full text, no truncation
                })
            elif "berbangkit" in perkara.lower() and not is_priority_section:
                new_state["MattersArising"].append({
                    "Perkara": f"Follow-up from: {perkara}",
                    "Keputusan": "Pelaksanaan",
                    "Keterangan": keterangan # Full text, no truncation
                })
        
        # Consolidation of Agenda 3 and 6 into "perkara-perkara berbangkit"
        berbangkit_items = []
        for ak in ["Agenda_3", "Agenda_6"]:
            if ak in json_data and isinstance(json_data[ak], dict):
                content = json_data[ak].get("Keterangan", "")
                if not content: continue
                
                # Split content into segments
                # Pattern: split by \n followed by list markers or @.
                pattern = r'(?:\n|^)\s*(?:[a-z]\.|\@\.)\s+'
                segments = re.split(pattern, content)
                
                for seg in segments:
                    seg = seg.strip()
                    if not seg: continue
                    # Avoid adding the general header usually found in Agenda 3
                    if "berikut telah dilaksanakan" in seg.lower() and len(seg) < 100:
                        continue
                    
                    # Extract the first sentence or bold part as the "item"
                    item_text = seg
                    outcome_text = ""
                    
                    # Try to find bolded part at start
                    match = re.search(r'^\*\*(.*?)\*\*', seg)
                    if match:
                        item_text = match.group(1)
                        outcome_text = seg[match.end():].strip().lstrip('.').strip()
                    else:
                        # Try first sentence
                        sentences = re.split(r'(?<=[.!?])\s+', seg, 1)
                        if len(sentences) > 1:
                            item_text = sentences[0]
                            outcome_text = sentences[1]
                    
                    record = {
                        "Perkara": item_text,
                        "Keputusan": "Pelaksanaan",
                        "Keterangan": outcome_text if outcome_text else seg
                    }
                    berbangkit_items.append(record)
                    
        # Add them to MattersArising to ensure visibility in the editor
        new_state["MattersArising"].extend(berbangkit_items)
                
    # Ingest Annex/Kembaran
    kembaran_key = find_key(json_data, "Kembaran")
    if kembaran_key:
        kembaran_data = json_data[kembaran_key]
        if isinstance(kembaran_data, dict):
            # If it's the de-facto format with Perkara: Markdown table
            new_state["Annex"] = kembaran_data.get("Perkara", "")
        else:
            new_state["Annex"] = str(kembaran_data)
            
    return new_state

def save_mom_to_json(state, filename):
    with open(filename, 'w') as f:
        json.dump(state, f, indent=4)
    return filename
