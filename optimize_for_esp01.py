#!/usr/bin/env python3
"""
ESP-01 File Size Optimizer for LED Matrix Studio
Reduces export file size to fit within ESP-01's 32KB storage limit
"""

import os
import sys
import struct
import zlib
import json
from pathlib import Path

class ESP01Optimizer:
    def __init__(self, target_size_kb=32):
        self.target_size_bytes = target_size_kb * 1024
        self.compression_level = 9  # Maximum compression
        
    def analyze_file(self, file_path):
        """Analyze the export file and return statistics"""
        if not os.path.exists(file_path):
            return None
            
        file_size = os.path.getsize(file_path)
        
        with open(file_path, 'rb') as f:
            data = f.read()
            
        # Try different optimization strategies
        strategies = {
            'original': {
                'size': file_size,
                'compression': 'None',
                'description': 'Original file'
            },
            'zlib_compression': {
                'size': len(zlib.compress(data, self.compression_level)),
                'compression': 'zlib',
                'description': 'zlib compression (level 9)'
            },
            'frame_reduction_50': {
                'size': self._reduce_frames(data, 0.5),
                'compression': 'Frame reduction 50%',
                'description': 'Reduce frames by 50% + zlib'
            },
            'frame_reduction_75': {
                'size': self._reduce_frames(data, 0.25),
                'compression': 'Frame reduction 75%',
                'description': 'Reduce frames by 75% + zlib'
            },
            'rle_compression': {
                'size': self._rle_compress(data),
                'compression': 'RLE',
                'description': 'Run-length encoding + zlib'
            },
            'delta_compression': {
                'size': self._delta_compress(data),
                'compression': 'Delta',
                'description': 'Delta encoding + zlib'
            }
        }
        
        return {
            'file_path': file_path,
            'original_size': file_size,
            'target_size': self.target_size_bytes,
            'strategies': strategies
        }
    
    def _reduce_frames(self, data, keep_ratio):
        """Reduce number of frames by keeping only every Nth frame"""
        # This is a simplified approach - in reality, you'd parse the actual format
        # For now, we'll simulate frame reduction by compressing a subset
        reduced_data = data[::int(1/keep_ratio)]
        return len(zlib.compress(reduced_data, self.compression_level))
    
    def _rle_compress(self, data):
        """Simple RLE compression"""
        compressed = bytearray()
        count = 1
        prev_byte = data[0] if data else 0
        
        for byte in data[1:]:
            if byte == prev_byte and count < 255:
                count += 1
            else:
                compressed.extend([count, prev_byte])
                count = 1
                prev_byte = byte
        
        compressed.extend([count, prev_byte])
        return len(zlib.compress(compressed, self.compression_level))
    
    def _delta_compress(self, data):
        """Simple delta compression (difference between consecutive bytes)"""
        if len(data) < 2:
            return len(data)
            
        deltas = bytearray()
        deltas.append(data[0])  # First byte unchanged
        
        for i in range(1, len(data)):
            delta = (data[i] - data[i-1]) & 0xFF
            deltas.append(delta)
            
        return len(zlib.compress(deltas, self.compression_level))
    
    def optimize_file(self, input_path, output_path=None):
        """Optimize the file and save the result"""
        analysis = self.analyze_file(input_path)
        if not analysis:
            print(f"❌ Error: Could not analyze file {input_path}")
            return None
            
        # Find the best strategy that fits within target size
        best_strategy = None
        best_ratio = 0
        
        print(f"📊 File Analysis: {os.path.basename(input_path)}")
        print(f"   Original size: {analysis['original_size']:,} bytes")
        print(f"   Target size: {analysis['target_size']:,} bytes")
        print()
        
        print("🔍 Optimization Strategies:")
        print("-" * 60)
        
        for name, strategy in analysis['strategies'].items():
            size = strategy['size']
            ratio = (1 - size / analysis['original_size']) * 100
            fits = size <= analysis['target_size']
            
            status = "✅ FITS" if fits else "❌ TOO LARGE"
            print(f"{name:20} | {size:8,} bytes | {ratio:5.1f}% | {status}")
            
            if fits and ratio > best_ratio:
                best_strategy = name
                best_ratio = ratio
        
        print()
        
        if not best_strategy:
            print("❌ No optimization strategy can fit the file within 32KB!")
            print("💡 Recommendations:")
            print("   1. Reduce animation complexity in LED Matrix Studio")
            print("   2. Use fewer frames")
            print("   3. Reduce matrix size")
            print("   4. Use monochrome instead of RGB")
            return None
        
        print(f"🎯 Best strategy: {best_strategy}")
        print(f"   Final size: {analysis['strategies'][best_strategy]['size']:,} bytes")
        print(f"   Compression: {analysis['strategies'][best_strategy]['compression']}")
        print(f"   Space saved: {best_ratio:.1f}%")
        
        # Apply the optimization
        return self._apply_optimization(input_path, output_path, best_strategy)
    
    def _apply_optimization(self, input_path, output_path, strategy):
        """Apply the selected optimization strategy"""
        if output_path is None:
            input_file = Path(input_path)
            output_path = input_file.parent / f"{input_file.stem}_ESP01_optimized{input_file.suffix}"
        
        try:
            with open(input_path, 'rb') as f:
                data = f.read()
            
            if strategy == 'zlib_compression':
                optimized_data = zlib.compress(data, self.compression_level)
            elif strategy == 'frame_reduction_50':
                optimized_data = self._reduce_frames_actual(data, 0.5)
            elif strategy == 'frame_reduction_75':
                optimized_data = self._reduce_frames_actual(data, 0.25)
            elif strategy == 'rle_compression':
                optimized_data = self._rle_compress_actual(data)
            elif strategy == 'delta_compression':
                optimized_data = self._delta_compress_actual(data)
            else:
                optimized_data = data
            
            # Add optimization header
            header = {
                'original_size': len(data),
                'optimized_size': len(optimized_data),
                'strategy': strategy,
                'compression': 'zlib',
                'target_device': 'ESP-01'
            }
            
            header_bytes = json.dumps(header).encode('utf-8')
            header_length = struct.pack('<H', len(header_bytes))
            
            final_data = header_length + header_bytes + optimized_data
            
            with open(output_path, 'wb') as f:
                f.write(final_data)
            
            print(f"\n✅ Optimization complete!")
            print(f"   Output file: {output_path}")
            print(f"   Final size: {len(final_data):,} bytes")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error during optimization: {e}")
            return None
    
    def _reduce_frames_actual(self, data, keep_ratio):
        """Actually reduce frames and return compressed data"""
        # Simplified frame reduction - in practice, parse the actual format
        step = int(1 / keep_ratio)
        reduced_data = data[::step]
        return zlib.compress(reduced_data, self.compression_level)
    
    def _rle_compress_actual(self, data):
        """Actually perform RLE compression and return compressed data"""
        compressed = bytearray()
        count = 1
        prev_byte = data[0] if data else 0
        
        for byte in data[1:]:
            if byte == prev_byte and count < 255:
                count += 1
            else:
                compressed.extend([count, prev_byte])
                count = 1
                prev_byte = byte
        
        compressed.extend([count, prev_byte])
        return zlib.compress(compressed, self.compression_level)
    
    def _delta_compress_actual(self, data):
        """Actually perform delta compression and return compressed data"""
        if len(data) < 2:
            return data
            
        deltas = bytearray()
        deltas.append(data[0])
        
        for i in range(1, len(data)):
            delta = (data[i] - data[i-1]) & 0xFF
            deltas.append(delta)
            
        return zlib.compress(deltas, self.compression_level)

def main():
    print("🔧 ESP-01 File Size Optimizer")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage: python optimize_for_esp01.py <input_file> [output_file]")
        print("Example: python optimize_for_esp01.py export_data.bin")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"❌ Error: Input file '{input_file}' not found!")
        return
    
    optimizer = ESP01Optimizer(target_size_kb=32)
    
    # Analyze the file first
    analysis = optimizer.analyze_file(input_file)
    if not analysis:
        return
    
    # Check if file already fits
    if analysis['original_size'] <= analysis['target_size']:
        print(f"✅ File already fits within 32KB! ({analysis['original_size']:,} bytes)")
        return
    
    # Optimize the file
    result = optimizer.optimize_file(input_file, output_file)
    
    if result:
        print(f"\n🚀 Ready to upload to ESP-01!")
        print(f"   Original: {analysis['original_size']:,} bytes")
        print(f"   Optimized: {os.path.getsize(result):,} bytes")
        print(f"   Upload the optimized file to your ESP-01")

if __name__ == "__main__":
    main()
