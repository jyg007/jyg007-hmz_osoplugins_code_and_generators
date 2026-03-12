host-attestation: 
  HKD-$MACHINE1:
    description:  $MACHINE1_DESCRIPTION
    host-key-doc: $MACHINE1_HKD_B24
  HKD-$MACHINE2:
    description:  $MACHINE2_DESCRIPTION
    host-key-doc: $MACHINE2_HKD_B24
crypto-pt: 
  lock: false
  index-1:
    type: secret
    domain-id: "$HSMDOMAIN1"
    secret: $SECRET_B24
    mkvp: $MKVP
  index-2:
    type: secret
    domain-id: "$HSMDOMAIN2"
    secret: $SECRET_B24
    mkvp: $MKVP
