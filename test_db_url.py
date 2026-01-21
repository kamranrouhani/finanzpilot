#!/usr/bin/env python3
"""Test the database URL transformation utility."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.shared.utils import transform_database_url

def test_database_url_transformation():
    """Test that the utility handles both postgresql:// and postgres:// schemes."""
    test_cases = [
        ('postgresql://user:pass@localhost:5432/db', 'postgresql+asyncpg://user:pass@localhost:5432/db'),
        ('postgres://user:pass@localhost:5432/db', 'postgresql+asyncpg://user:pass@localhost:5432/db'),
        ('postgresql://user:pass@host.com:5432/database_name', 'postgresql+asyncpg://user:pass@host.com:5432/database_name'),
        ('postgres://user:pass@host.com:5432/database_name', 'postgresql+asyncpg://user:pass@host.com:5432/database_name'),
    ]

    print('Testing database URL transformation:')
    all_passed = True

    for input_url, expected_url in test_cases:
        result = transform_database_url(input_url)
        passed = result == expected_url
        status = '✓' if passed else '✗'
        print(f'{status} {input_url}')
        print(f'  Expected: {expected_url}')
        print(f'  Got:      {result}')
        if not passed:
            all_passed = False
        print()

    return all_passed

if __name__ == '__main__':
    success = test_database_url_transformation()
    sys.exit(0 if success else 1)
