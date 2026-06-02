"""
Algorithm Knowledge Tank - Backend Information Storage
Indexes and serves algorithm files and structured training knowledge to MoE agents.

Two knowledge sources:
  1. Algorithm files (*.py, *.cs, etc.) — scanned and indexed from the algorithms/ directory
  2. Training JSON files (training/*.json) — structured domain knowledge loaded directly
"""

import os
import json
import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import re

# Resolve paths relative to this file so hardcoded /home/chewlo paths are no longer needed
_HERE = Path(__file__).resolve().parent
_DEFAULT_ALGORITHMS_PATH = str(_HERE / "algorithms")
_DEFAULT_DB_PATH = str(_HERE / "knowledge_tank.db")
_DEFAULT_TRAINING_DIR = str(_HERE / "training")

@dataclass
class AlgorithmMetadata:
    """Metadata for a single algorithm"""
    id: str
    name: str
    path: str
    category: str
    subcategory: str
    file_type: str
    size: int
    description: str
    tags: List[str]
    dependencies: List[str]
    complexity: Optional[str] = None
    use_cases: List[str] = None
    indexed_at: str = None
    
    def to_dict(self):
        return asdict(self)

class AlgorithmScanner:
    """Scans and indexes algorithm files"""
    
    # Category detection patterns
    CATEGORIES = {
        'cryptography': ['cipher', 'encrypt', 'decrypt', 'crypto', 'rsa', 'aes'],
        'machine_learning': ['ml', 'neural', 'train', 'model', 'regression', 'classification'],
        'graphs': ['graph', 'dijkstra', 'bfs', 'dfs', 'tree', 'path'],
        'data_structures': ['array', 'linked', 'stack', 'queue', 'heap', 'trie'],
        'dynamic_programming': ['dp', 'knapsack', 'fibonacci', 'memo'],
        'mathematics': ['prime', 'factorial', 'gcd', 'lcm', 'math'],
        'sorting': ['sort', 'merge', 'quick', 'bubble', 'heap'],
        'searching': ['search', 'binary', 'linear'],
        'hashing': ['hash', 'md5', 'sha'],
        'image_processing': ['image', 'pixel', 'filter', 'compression'],
        'network': ['socket', 'tcp', 'udp', 'http', 'ftp']
    }
    
    def __init__(self, base_path: str = _DEFAULT_ALGORITHMS_PATH):
        self.base_path = Path(base_path)
        
    def scan_file(self, filepath: Path) -> Optional[AlgorithmMetadata]:
        """Scan single file and extract metadata"""
        try:
            relative_path = filepath.relative_to(self.base_path)
            
            # Extract category from directory structure
            parts = relative_path.parts
            category = parts[0] if len(parts) > 0 else "general"
            subcategory = parts[1] if len(parts) > 1 else "general"
            
            # Generate unique ID
            algo_id = hashlib.md5(str(relative_path).encode()).hexdigest()[:12]
            
            # Extract description from file
            description = self._extract_description(filepath)
            
            # Detect tags
            tags = self._detect_tags(filepath, description)
            
            # Extract dependencies
            dependencies = self._extract_imports(filepath)
            
            # Get file stats
            stat = filepath.stat()
            
            return AlgorithmMetadata(
                id=algo_id,
                name=filepath.stem,
                path=str(relative_path),
                category=category,
                subcategory=subcategory,
                file_type=filepath.suffix,
                size=stat.st_size,
                description=description,
                tags=tags,
                dependencies=dependencies,
                indexed_at=datetime.now().isoformat()
            )
        except Exception as e:
            print(f"Error scanning {filepath}: {e}")
            return None
    
    def _extract_description(self, filepath: Path) -> str:
        """Extract description from file docstring or comments"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2000)  # First 2000 chars
                
                ext = filepath.suffix
                
                # Python - docstrings
                if ext == '.py':
                    docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                    if docstring_match:
                        return docstring_match.group(1).strip()[:500]
                    
                    comment_match = re.search(r'#\s+(.*?)(?:\n\n|\n[^#])', content, re.DOTALL)
                    if comment_match:
                        return comment_match.group(1).strip()[:500]
                
                # C#, Java, C++, JavaScript - // or /* */ comments
                elif ext in ['.cs', '.java', '.cpp', '.c', '.js', '.go', '.rs']:
                    # Multi-line comment
                    comment_match = re.search(r'/\*(.*?)\*/', content, re.DOTALL)
                    if comment_match:
                        return comment_match.group(1).strip()[:500]
                    
                    # Single-line comments
                    comment_match = re.search(r'//\s+(.*?)(?:\n\n|\n[^/])', content, re.DOTALL)
                    if comment_match:
                        return comment_match.group(1).strip()[:500]
                
                # Ruby, PHP - # comments
                elif ext in ['.rb', '.php']:
                    comment_match = re.search(r'#\s+(.*?)(?:\n\n|\n[^#])', content, re.DOTALL)
                    if comment_match:
                        return comment_match.group(1).strip()[:500]
                
                return filepath.stem.replace('_', ' ').replace('-', ' ').title()
        except:
            return filepath.stem.replace('_', ' ').replace('-', ' ').title()
    
    def _detect_tags(self, filepath: Path, description: str) -> List[str]:
        """Detect relevant tags from filename and content"""
        tags = set()
        
        text = (filepath.stem + " " + description).lower()
        
        for category, keywords in self.CATEGORIES.items():
            if any(kw in text for kw in keywords):
                tags.add(category)
        
        return list(tags)
    
    def _extract_imports(self, filepath: Path) -> List[str]:
        """Extract imports/dependencies from file"""
        deps = set()
        ext = filepath.suffix
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Python imports
                if ext == '.py':
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('import ') or line.startswith('from '):
                            match = re.match(r'(?:from|import)\s+([a-zA-Z0-9_\.]+)', line)
                            if match:
                                module = match.group(1).split('.')[0]
                                deps.add(module)
                
                # C# using statements
                elif ext == '.cs':
                    for match in re.finditer(r'using\s+([a-zA-Z0-9_\.]+);', content):
                        deps.add(match.group(1).split('.')[0])
                
                # JavaScript/Node imports
                elif ext == '.js':
                    for match in re.finditer(r'(?:import|require)\s*\(?[\'"]([a-zA-Z0-9_\-@/]+)', content):
                        deps.add(match.group(1).split('/')[0])
                
                # Java imports
                elif ext == '.java':
                    for match in re.finditer(r'import\s+([a-zA-Z0-9_\.]+);', content):
                        deps.add(match.group(1).split('.')[0])
                
                # C/C++ includes
                elif ext in ['.c', '.cpp', '.h', '.hpp']:
                    for match in re.finditer(r'#include\s+[<"]([a-zA-Z0-9_\.]+)', content):
                        deps.add(match.group(1))
        except:
            pass
        
        return list(deps)
    
    def scan_directory(self, max_files: Optional[int] = None) -> List[AlgorithmMetadata]:
        """Scan entire algorithm directory"""
        algorithms = []
        count = 0
        
        # File extensions to index
        extensions = {'.py', '.cs', '.js', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php'}
        
        print(f"Scanning {self.base_path}...")
        
        for root, dirs, files in os.walk(self.base_path):
            # Skip common non-algorithm directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules', '.git', 'bin', 'obj']]
            
            for filename in files:
                # Check if it's an algorithm file
                if any(filename.endswith(ext) for ext in extensions) and not filename.startswith('__'):
                    filepath = Path(root) / filename
                    
                    metadata = self.scan_file(filepath)
                    if metadata:
                        algorithms.append(metadata)
                        count += 1
                        
                        if count % 100 == 0:
                            print(f"  Indexed {count} algorithms...")
                        
                        if max_files and count >= max_files:
                            print(f"Reached max files limit: {max_files}")
                            return algorithms
        
        print(f"✓ Scanned {count} algorithms")
        return algorithms

class KnowledgeTank:
    """Backend storage for algorithm and training knowledge"""

    def __init__(self, db_path: str = _DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create algorithms table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS algorithms (
                id TEXT PRIMARY KEY,
                name TEXT,
                path TEXT UNIQUE,
                category TEXT,
                subcategory TEXT,
                file_type TEXT,
                size INTEGER,
                description TEXT,
                tags TEXT,
                dependencies TEXT,
                complexity TEXT,
                use_cases TEXT,
                indexed_at TEXT
            )
        ''')
        
        # Create search index
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON algorithms(category)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tags ON algorithms(tags)
        ''')
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS algorithms_fts 
            USING fts5(name, description, tags, content=algorithms)
        ''')
        
        # Training knowledge table — structured JSON entries from training/*.json
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training (
                id TEXT PRIMARY KEY,
                title TEXT,
                category TEXT,
                subcategory TEXT,
                description TEXT,
                content TEXT,
                tags TEXT,
                source_file TEXT,
                indexed_at TEXT
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_training_category ON training(category)
        ''')
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS training_fts
            USING fts5(title, description, content, tags, content=training)
        ''')

        conn.commit()
        conn.close()
        print(f"✓ Knowledge Tank initialized: {self.db_path}")

    # ------------------------------------------------------------------
    # Training knowledge loading
    # ------------------------------------------------------------------

    def load_training_files(self, training_dir: str = _DEFAULT_TRAINING_DIR) -> int:
        """Load all JSON files from training_dir into the training table.

        Each JSON file should be a list of knowledge entries with at minimum:
          - "id"          : unique string identifier
          - "title"       : human-readable name
          - "category"    : broad domain (e.g. 'algorithms', 'reasoning')
          - "description" : concise explanation
        Optional but indexed: "subcategory", "tags", "key_insight", "use_cases",
          "code_template", "complexity", "process", "example"

        Returns:
            Total number of entries loaded.
        """
        path = Path(training_dir)
        if not path.exists():
            print(f"Training directory not found: {training_dir}")
            return 0

        total = 0
        for json_file in sorted(path.glob("*.json")):
            try:
                with open(json_file) as fh:
                    entries = json.load(fh)
                count = self._index_training_entries(entries, str(json_file))
                print(f"  Loaded {count:3d} entries from {json_file.name}")
                total += count
            except Exception as exc:
                print(f"  ERROR loading {json_file.name}: {exc}")

        print(f"✓ Training knowledge loaded: {total} total entries from {training_dir}")
        return total

    def _index_training_entries(self, entries: list, source_file: str) -> int:
        """Insert a list of training entry dicts into the training table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        count = 0

        for entry in entries:
            entry_id = entry.get("id")
            if not entry_id:
                continue

            # Serialise all non-metadata fields as content for FTS so every
            # entry is fully searchable regardless of which keys it uses.
            skip_keys = {"id", "title", "category", "subcategory", "description",
                         "tags", "source_file", "indexed_at"}
            content_parts = []
            for key, val in entry.items():
                if key not in skip_keys and val:
                    content_parts.append(str(val))
            content = " | ".join(content_parts)

            tags = entry.get("tags", [])
            tags_str = json.dumps(tags) if isinstance(tags, list) else str(tags)

            cursor.execute('''
                INSERT OR REPLACE INTO training
                  (id, title, category, subcategory, description, content, tags, source_file, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_id,
                entry.get("title", entry_id),
                entry.get("category", "general"),
                entry.get("subcategory", ""),
                entry.get("description", ""),
                content,
                tags_str,
                source_file,
                datetime.now().isoformat()
            ))

            # Refresh FTS index
            cursor.execute('''
                INSERT OR REPLACE INTO training_fts(rowid, title, description, content, tags)
                SELECT rowid, title, description, content, tags FROM training WHERE id = ?
            ''', (entry_id,))

            count += 1

        conn.commit()
        conn.close()
        return count

    def search_training(self, query: str, category: Optional[str] = None,
                        limit: int = 10) -> List[Dict]:
        """Full-text search over training knowledge entries.

        Args:
            query: Search terms (supports SQLite FTS5 query syntax).
            category: Optional category filter.
            limit: Maximum results to return.

        Returns:
            List of matching entry dicts with keys: id, title, category,
            subcategory, description, tags.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if category:
                cursor.execute('''
                    SELECT t.id, t.title, t.category, t.subcategory, t.description, t.tags
                    FROM training t
                    JOIN training_fts fts ON t.rowid = fts.rowid
                    WHERE training_fts MATCH ? AND t.category = ?
                    LIMIT ?
                ''', (query, category, limit))
            else:
                cursor.execute('''
                    SELECT t.id, t.title, t.category, t.subcategory, t.description, t.tags
                    FROM training t
                    JOIN training_fts fts ON t.rowid = fts.rowid
                    WHERE training_fts MATCH ?
                    LIMIT ?
                ''', (query, limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "title": row[1],
                    "category": row[2],
                    "subcategory": row[3],
                    "description": row[4],
                    "tags": json.loads(row[5]) if row[5] else []
                })
        except sqlite3.OperationalError:
            results = []

        conn.close()
        return results

    def get_training_entry(self, entry_id: str) -> Optional[Dict]:
        """Retrieve a single training entry by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM training WHERE id = ?', (entry_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0], "title": row[1], "category": row[2],
            "subcategory": row[3], "description": row[4],
            "content": row[5],
            "tags": json.loads(row[6]) if row[6] else []
        }

    def get_training_stats(self) -> Dict:
        """Return statistics about the loaded training knowledge."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM training')
        total = cursor.fetchone()[0]
        cursor.execute('''
            SELECT category, COUNT(*) FROM training
            GROUP BY category ORDER BY COUNT(*) DESC
        ''')
        by_category = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return {"total_training_entries": total, "by_category": by_category}

    def index_algorithm(self, algo: AlgorithmMetadata):
        """Add algorithm to knowledge tank"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO algorithms VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            algo.id,
            algo.name,
            algo.path,
            algo.category,
            algo.subcategory,
            algo.file_type,
            algo.size,
            algo.description,
            json.dumps(algo.tags),
            json.dumps(algo.dependencies),
            algo.complexity,
            json.dumps(algo.use_cases) if algo.use_cases else None,
            algo.indexed_at
        ))
        
        # Update FTS index
        cursor.execute('''
            INSERT OR REPLACE INTO algorithms_fts(rowid, name, description, tags)
            SELECT rowid, name, description, tags FROM algorithms WHERE id = ?
        ''', (algo.id,))
        
        conn.commit()
        conn.close()
    
    def index_batch(self, algorithms: List[AlgorithmMetadata]):
        """Bulk index algorithms"""
        print(f"Indexing {len(algorithms)} algorithms...")
        
        for i, algo in enumerate(algorithms):
            self.index_algorithm(algo)
            if (i + 1) % 1000 == 0:
                print(f"  Indexed {i + 1}/{len(algorithms)}")
        
        print(f"✓ Indexed {len(algorithms)} algorithms")
    
    def search(self, query: str, category: Optional[str] = None, 
               limit: int = 10) -> List[Dict]:
        """Search algorithms by query"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            # Category-filtered search
            cursor.execute('''
                SELECT a.* FROM algorithms a
                JOIN algorithms_fts fts ON a.rowid = fts.rowid
                WHERE algorithms_fts MATCH ? AND a.category = ?
                LIMIT ?
            ''', (query, category, limit))
        else:
            # Full-text search
            cursor.execute('''
                SELECT a.* FROM algorithms a
                JOIN algorithms_fts fts ON a.rowid = fts.rowid
                WHERE algorithms_fts MATCH ?
                LIMIT ?
            ''', (query, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'name': row[1],
                'path': row[2],
                'category': row[3],
                'subcategory': row[4],
                'description': row[7],
                'tags': json.loads(row[8]) if row[8] else []
            })
        
        conn.close()
        return results
    
    def get_by_category(self, category: str, limit: int = 100) -> List[Dict]:
        """Get all algorithms in a category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, path, category, subcategory, description, tags
            FROM algorithms WHERE category = ? LIMIT ?
        ''', (category, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'name': row[1],
                'path': row[2],
                'category': row[3],
                'subcategory': row[4],
                'description': row[5],
                'tags': json.loads(row[6]) if row[6] else []
            })
        
        conn.close()
        return results
    
    def get_by_id(self, algo_id: str) -> Optional[Dict]:
        """Get algorithm by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM algorithms WHERE id = ?', (algo_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'name': row[1],
            'path': row[2],
            'category': row[3],
            'subcategory': row[4],
            'file_type': row[5],
            'size': row[6],
            'description': row[7],
            'tags': json.loads(row[8]) if row[8] else [],
            'dependencies': json.loads(row[9]) if row[9] else []
        }
    
    def get_stats(self) -> Dict:
        """Get knowledge tank statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total count
        cursor.execute('SELECT COUNT(*) FROM algorithms')
        total = cursor.fetchone()[0]
        
        # By category
        cursor.execute('''
            SELECT category, COUNT(*) 
            FROM algorithms 
            GROUP BY category 
            ORDER BY COUNT(*) DESC
        ''')
        by_category = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By file type
        cursor.execute('''
            SELECT file_type, COUNT(*) 
            FROM algorithms 
            GROUP BY file_type
        ''')
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total_algorithms': total,
            'by_category': by_category,
            'by_file_type': by_type
        }
    
    def export_to_json(self, output_path: str):
        """Export entire knowledge base to JSON"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM algorithms')
        
        algorithms = []
        for row in cursor.fetchall():
            algorithms.append({
                'id': row[0],
                'name': row[1],
                'path': row[2],
                'category': row[3],
                'subcategory': row[4],
                'file_type': row[5],
                'size': row[6],
                'description': row[7],
                'tags': json.loads(row[8]) if row[8] else [],
                'dependencies': json.loads(row[9]) if row[9] else []
            })
        
        conn.close()
        
        with open(output_path, 'w') as f:
            json.dump(algorithms, f, indent=2)
        
        print(f"✓ Exported {len(algorithms)} algorithms to {output_path}")

# Build the knowledge tank
if __name__ == "__main__":
    print("=== Building Algorithm Knowledge Tank ===\n")

    tank = KnowledgeTank()

    # Load structured training knowledge from training/*.json
    print("\n--- Loading training knowledge files ---")
    tank.load_training_files()
    t_stats = tank.get_training_stats()
    print(f"\nTraining entries: {t_stats['total_training_entries']}")
    print("By category:", t_stats["by_category"])

    # Scan and index algorithm code files
    print("\n--- Scanning algorithm files ---")
    scanner = AlgorithmScanner()
    algorithms = scanner.scan_directory(max_files=None)
    tank.index_batch(algorithms)

    # Show algorithm stats
    print("\n=== Algorithm Stats ===")
    stats = tank.get_stats()
    print(f"Total Algorithms: {stats['total_algorithms']}")
    print("\nBy Category:")
    for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1])[:10]:
        print(f"  {cat}: {count}")

    # Test search
    print("\n=== Testing Algorithm Search ===")
    results = tank.search("encryption rsa")
    print(f"Found {len(results)} results for 'encryption rsa':")
    for r in results[:5]:
        print(f"  - {r['name']} ({r['category']})")

    print("\n=== Testing Training Search ===")
    results = tank.search_training("binary search sorted array")
    print(f"Found {len(results)} training results for 'binary search sorted array':")
    for r in results[:5]:
        print(f"  - {r['title']} ({r['category']}/{r['subcategory']})")

    print("\n✓ Knowledge Tank ready!")

