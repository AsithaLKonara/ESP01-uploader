#!/usr/bin/env python3
"""
token_generator.py
Generate HMAC-SHA1 tokens for ESP-01 authentication

This script generates secure tokens that can be used with the X-Upload-Token header
when uploading files or metadata to the ESP-01.

Usage:
  python token_generator.py --secret "your_secret_key" --ttl 90
  python token_generator.py --secret "your_secret_key" --generate-multiple 5
"""

import argparse
import hmac
import hashlib
import time
import json

def generate_token(secret, timestamp=None):
    """
    Generate HMAC-SHA1 token for ESP-01 authentication
    
    Args:
        secret (str): Secret key (must match TOKEN_SECRET on ESP-01)
        timestamp (int, optional): Unix timestamp. If None, uses current time.
    
    Returns:
        str: Token in format "hex_hmac:timestamp"
    """
    if timestamp is None:
        timestamp = int(time.time())
    
    # Create HMAC-SHA1 digest
    digest = hmac.new(secret.encode('utf-8'), str(timestamp).encode('utf-8'), hashlib.sha1).hexdigest()
    
    # Return token in format "hex_hmac:timestamp"
    return f"{digest}:{timestamp}"

def generate_multiple_tokens(secret, count=5, interval_seconds=30):
    """
    Generate multiple tokens with different timestamps
    
    Args:
        secret (str): Secret key
        count (int): Number of tokens to generate
        interval_seconds (int): Time interval between tokens
    
    Returns:
        list: List of token dictionaries
    """
    tokens = []
    current_time = int(time.time())
    
    for i in range(count):
        timestamp = current_time + (i * interval_seconds)
        token = generate_token(secret, timestamp)
        
        # Calculate expiration time
        expiration = timestamp + 90  # 90 second TTL
        
        token_info = {
            "token": token,
            "timestamp": timestamp,
            "expires_at": expiration,
            "expires_in_seconds": expiration - current_time,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        }
        
        tokens.append(token_info)
    
    return tokens

def verify_token_format(token):
    """
    Verify that a token has the correct format
    
    Args:
        token (str): Token to verify
    
    Returns:
        bool: True if format is correct
    """
    try:
        parts = token.split(':')
        if len(parts) != 2:
            return False
        
        hex_part, timestamp_part = parts
        
        # Check hex format (40 characters for SHA1)
        if len(hex_part) != 40:
            return False
        
        # Check if hex_part is valid hexadecimal
        int(hex_part, 16)
        
        # Check timestamp format
        timestamp = int(timestamp_part)
        if timestamp <= 0:
            return False
        
        return True
    except (ValueError, IndexError):
        return False

def main():
    parser = argparse.ArgumentParser(description='Generate HMAC-SHA1 tokens for ESP-01 authentication')
    parser.add_argument('--secret', required=True, help='Secret key (must match TOKEN_SECRET on ESP-01)')
    parser.add_argument('--ttl', type=int, default=90, help='Token TTL in seconds (default: 90)')
    parser.add_argument('--generate-multiple', type=int, metavar='COUNT', help='Generate multiple tokens')
    parser.add_argument('--interval', type=int, default=30, help='Interval between multiple tokens in seconds (default: 30)')
    parser.add_argument('--verify', metavar='TOKEN', help='Verify token format')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    if args.verify:
        # Verify token format
        if verify_token_format(args.verify):
            print("✅ Token format is valid")
            parts = args.verify.split(':')
            print(f"   HMAC: {parts[0]}")
            print(f"   Timestamp: {parts[1]}")
            print(f"   Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(parts[1])))}")
        else:
            print("❌ Token format is invalid")
        return
    
    if args.generate_multiple:
        # Generate multiple tokens
        tokens = generate_multiple_tokens(args.secret, args.generate_multiple, args.interval)
        
        if args.json:
            # Output as JSON
            output = {
                "secret": args.secret,
                "ttl_seconds": args.ttl,
                "tokens": tokens
            }
            print(json.dumps(output, indent=2))
        else:
            # Output as human-readable text
            print(f"🔑 Generated {len(tokens)} tokens with secret: {args.secret}")
            print(f"⏰ TTL: {args.ttl} seconds")
            print(f"📅 Interval: {args.interval} seconds")
            print()
            
            for i, token_info in enumerate(tokens, 1):
                print(f"Token {i}:")
                print(f"  Value: {token_info['token']}")
                print(f"  Created: {token_info['created_at']}")
                print(f"  Expires: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(token_info['expires_at']))}")
                print(f"  Valid for: {token_info['expires_in_seconds']} more seconds")
                print()
    else:
        # Generate single token
        token = generate_token(args.secret)
        expiration = int(time.time()) + args.ttl
        
        if args.json:
            # Output as JSON
            output = {
                "token": token,
                "secret": args.secret,
                "ttl_seconds": args.ttl,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "expires_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expiration))
            }
            print(json.dumps(output, indent=2))
        else:
            # Output as human-readable text
            print(f"🔑 Generated token for secret: {args.secret}")
            print(f"⏰ TTL: {args.ttl} seconds")
            print()
            print(f"Token: {token}")
            print()
            print(f"Usage:")
            print(f"  curl -H 'X-Upload-Token: {token}' http://192.168.4.1/upload")
            print(f"  curl -H 'X-Upload-Token: {token}' http://192.168.4.1/upload-metadata")
            print()
            print(f"Created: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Expires: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expiration))}")

if __name__ == '__main__':
    main()
