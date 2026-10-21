"""Verify both inventories and run the original v1.0 archive verifier."""
from v1_1.archive import check_layer, legacy_checks

if __name__ == '__main__':
    check_layer()
    legacy_checks(['verify'])
    print('ARCHIVE 1.1.0 VERIFIED')
