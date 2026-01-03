import subprocess
import os
import sys
import json

QUARTO_PATH = "/usr/share/positron/resources/app/quarto/bin/quarto"

def generate_mom(json_path, output_format="pdf", output_file=None):
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    # Extract some metadata for the Quarto render
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    
    if not isinstance(data, dict):
        print(f"Error: Invalid JSON structure in {json_path}. Expected dict or list of dicts.")
        return
    
    siri = data.get("Siri", "N/A")
    tarikh = data.get("Tarikh", "N/A")
    jenis = data.get("Jenis", "agm") # Default to agm if not specified
    
    if jenis == "exco":
        title_text = "MINIT MESYUARAT JAWATANKUASA EKSEKUTIF"
    else:
        title_text = "MINIT MESYUARAT AGONG TAHUNAN"

    year_part = tarikh.split("/")[-1] if "/" in tarikh else "2025"
    tahun = year_part if len(year_part) == 4 else "20" + year_part

    # Handle Typst as an alternative to LaTeX for PDF
    quarto_format = output_format
    if output_format == "typst":
        template = "mom_template_typ.qmd"
        ext = "pdf" # Typst generates PDF
    else:
        template = "mom_template.qmd"
        ext = output_format

    if not output_file:
        output_base = os.path.splitext(os.path.basename(json_path))[0]
        if output_format == "typst":
             output_file = f"{output_base}_typst.pdf"
        else:
            output_file = f"{output_base}.{ext}"

    # Quarto's --output flag does not like absolute paths.
    local_output = f"temp_output.{ext}"
    
    env = os.environ.copy()
    env["MOM_JSON_FILE"] = os.path.abspath(json_path)

    cmd = [
        QUARTO_PATH,
        "render",
        template,
        "--to", quarto_format,
        "--output", local_output,
        "-M", f"siri:{siri}",
        "-M", f"tarikh:{tarikh}",
        "-M", f"tahun:{tahun}",
        "-M", f"jenis:{jenis}",
        "-M", f"mtitle:{title_text}"
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    if result.returncode == 0:
        if os.path.exists(local_output):
            import shutil
            # Ensure the destination directory exists (for absolute paths in /tmp etc)
            dest_dir = os.path.dirname(os.path.abspath(output_file))
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            
            shutil.move(local_output, output_file)
            print(f"Successfully generated {output_file}")
    else:
        print(f"Error generating {output_format.upper()}:")
        print(result.stdout)
        print(result.stderr)
        # Cleanup local output if it was created but move failed or process error
        if os.path.exists(local_output):
            os.remove(local_output)
    
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_mom.py <input_json> [pdf|docx]")
    else:
        fmt = sys.argv[2] if len(sys.argv) > 2 else "pdf"
        generate_mom(sys.argv[1], fmt)
