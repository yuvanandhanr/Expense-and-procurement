import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

export interface OCRGroundTruth {
    file: string;
    category: string;
    party_name: string;
    doc_no: string;
    doc_date: string;
    n_items: string;
    subtotal: string;
    tax_amount: string;
    grand_total: string;
    ref_no: string;
}

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OCR_DATASET_PATH = process.env.OCR_DATASET_PATH || path.resolve(__dirname, '../../../test-dataset');
const GROUND_TRUTH_FILE = path.join(OCR_DATASET_PATH, 'ground_truth.csv');

let cachedGroundTruth: OCRGroundTruth[] | null = null;

export function getGroundTruth(): OCRGroundTruth[] {
    if (cachedGroundTruth) {
        return cachedGroundTruth;
    }

    const content = fs.readFileSync(GROUND_TRUTH_FILE, 'utf-8');
    const lines = content.split('\n').filter(line => line.trim().length > 0);
    const headers = lines[0].split(',');

    cachedGroundTruth = lines.slice(1).map(line => {
        const values = line.split(',');
        return {
            file: values[0].replace(/\\/g, '/'),
            category: values[1],
            party_name: values[2],
            doc_no: values[3],
            doc_date: values[4],
            n_items: values[5],
            subtotal: values[6],
            tax_amount: values[7],
            grand_total: values[8],
            ref_no: values[9],
        };
    });

    return cachedGroundTruth;
}

export function getRandomTestImage(category: 'reimbursement' | 'vendor_invoice' | 'procurement_grn'): OCRGroundTruth {
    const data = getGroundTruth();
    const filtered = data.filter(item => item.category === category);
    if (filtered.length === 0) {
        throw new Error(`No OCR images found for category: ${category}`);
    }
    const randomIndex = Math.floor(Math.random() * filtered.length);
    return filtered[randomIndex];
}

export function getImagePath(fileRelativePath: string): string {
    const withImages = path.join(OCR_DATASET_PATH, 'images', fileRelativePath);
    const sourcePath = fs.existsSync(withImages) ? withImages : path.join(OCR_DATASET_PATH, fileRelativePath);

    // Create a copy with unique trailing bytes to prevent duplicate content_hash rejection in repeated test runs
    const tempDir = path.join(OCR_DATASET_PATH, '.temp');
    if (!fs.existsSync(tempDir)) {
        fs.mkdirSync(tempDir, { recursive: true });
    }
    const ext = path.extname(sourcePath);
    const basename = path.basename(sourcePath, ext);
    const uniquePath = path.join(tempDir, `${basename}_${Date.now()}_${Math.random().toString(36).substring(2, 7)}${ext}`);
    fs.copyFileSync(sourcePath, uniquePath);
    fs.appendFileSync(uniquePath, Buffer.from(`\n# test_run_${Date.now()}_${Math.random()}`));
    return uniquePath;
}
