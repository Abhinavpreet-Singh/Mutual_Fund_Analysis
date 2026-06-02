# Day 2 Query Results

## Q1: Top 5 funds by AUM

Rows returned: 5

 amfi_code                                           scheme_name        fund_house  aum_crore  expense_ratio_pct      risk_grade
    148568 Mirae Asset Emerging Bluechip Fund - Regular - Growth    Mirae Asset MF      49046               1.52 Moderately High
    120842         Kotak Emerging Equity Fund - Regular - Growth Kotak Mahindra MF      47469               1.56            High
    118634        Nippon India Small Cap Fund - Regular - Growth   Nippon India MF      43630               1.53       Very High
    149322            DSP Top 100 Equity Fund - Regular - Growth   DSP Mutual Fund      41828               1.54        Moderate
    102886                   UTI Mid Cap Fund - Regular - Growth   UTI Mutual Fund      41728               1.51            High

---

## Q2: Average NAV per month

Rows returned: 53

  month  avg_nav
2022-01 207.0614
2022-02 207.7178
2022-03 209.6926
2022-04 211.8335
2022-05 212.7315
2022-06 213.8609
2022-07 213.9561
2022-08 215.6840
2022-09 218.4943
2022-10 219.5296
2022-11 223.4707
2022-12 226.7606
2023-01 230.6712
2023-02 233.8477
2023-03 238.0096
2023-04 240.6133
2023-05 241.8929
2023-06 244.6055
2023-07 245.7807
2023-08 247.7346
2023-09 251.8337
2023-10 255.6070
2023-11 258.3525
2023-12 262.0203
2024-01 264.6206
2024-02 266.3317
2024-03 269.5978
2024-04 271.3000
2024-05 273.4505
2024-06 275.4655
2024-07 279.0241
2024-08 279.7361
2024-09 281.0170
2024-10 282.1278
2024-11 285.2436
2024-12 285.2726
2025-01 288.0384
2025-02 291.7446
2025-03 296.1581
2025-04 299.4130
2025-05 303.9397
2025-06 306.8799
2025-07 309.7263
2025-08 313.1804
2025-09 316.1320
2025-10 321.4500
2025-11 325.6812
2025-12 331.7330
2026-01 337.1175
2026-02 342.0764
2026-03 347.1875
2026-04 355.0254
2026-05 357.0392

---

## Q3: SIP inflow YoY growth

Rows returned: 3

year  avg_yoy_growth_pct  total_sip_inflow_crore
2023               23.49                184763.0
2024               45.69                269781.0
2025               25.19                335740.0

---

## Q4: Transactions by state

Rows returned: 10

         state  transaction_count  total_amount_inr  avg_amount_inr
        Punjab               2965       315780459.0       106502.68
    Tamil Nadu               2806       315177237.0       112322.61
Madhya Pradesh               2931       308312493.0       105190.21
     Rajasthan               2577       298645822.0       115888.95
       Gujarat               2780       298358940.0       107323.36
   West Bengal               2748       297182514.0       108145.02
     Telangana               2718       290219284.0       106776.78
         Delhi               2677       289633404.0       108193.28
 Uttar Pradesh               2695       285368873.0       105888.26
       Haryana               2736       279634354.0       102205.54

---

## Q5: Funds with expense_ratio < 1%

Rows returned: 14

 amfi_code                                          scheme_name               fund_house category variant_type  expense_ratio_pct
    118636 Nippon India Gilt Securities Fund - Regular - Growth          Nippon India MF     Debt      Regular               0.55
    100025         HDFC Short Term Debt Fund - Regular - Growth         HDFC Mutual Fund     Debt      Regular               0.56
    120844                 Kotak Liquid Fund - Regular - Growth        Kotak Mahindra MF     Debt      Regular               0.60
    119552             SBI Bluechip Fund - Direct Plan - Growth          SBI Mutual Fund   Equity       Direct               0.66
    118633        Nippon India Large Cap Fund - Direct - Growth          Nippon India MF   Equity       Direct               0.72
    119599            SBI Small Cap Fund - Direct Plan - Growth          SBI Mutual Fund   Equity       Direct               0.72
    120507             ICICI Pru Liquid Fund - Regular - Growth      ICICI Prudential MF     Debt      Regular               0.74
    119093                 Axis Bluechip Fund - Direct - Growth         Axis Mutual Fund   Equity       Direct               0.75
    119120         SBI Magnum Gilt Fund - Regular Plan - Growth          SBI Mutual Fund     Debt      Regular               0.77
    125498    HDFC Mid-Cap Opportunities Fund - Direct - Growth         HDFC Mutual Fund   Equity       Direct               0.78
    101208                  ABSL Liquid Fund - Regular - Growth Aditya Birla Sun Life MF     Debt      Regular               0.79
    120504            ICICI Pru Bluechip Fund - Direct - Growth      ICICI Prudential MF   Equity       Direct               0.80
    118635                       Nippon India ETF Nifty 50 BeES          Nippon India MF   Equity       Direct               0.89
    125497             HDFC Top 100 Fund - Direct Plan - Growth         HDFC Mutual Fund   Equity       Direct               0.92

---

## Q6: Average 3-year return by category

Rows returned: 12

       category  avg_return_3yr_pct  avg_benchmark_3yr_pct  avg_alpha
      Small Cap               21.69                  20.65       1.03
        Mid Cap               16.59                  15.42       1.17
      Flexi Cap               15.50                  13.68       1.82
          Value               14.76                  14.21       0.55
Large & Mid Cap               14.56                  12.86       1.70
           ELSS               13.58                  13.04       0.54
      Large Cap               12.99                  11.73       1.25
          Index               12.10                  11.17       0.93
      Index/ETF               11.77                   9.97       1.80
 Short Duration                7.37                   5.39       1.98
         Liquid                6.33                   4.82       1.52
           Gilt                5.69                   4.45       1.25

---

## Q7: Top 10 funds by Sharpe ratio

Rows returned: 10

                                         scheme_name               fund_house       category variant_type  sharpe_ratio  sortino_ratio  expense_ratio_pct
            ICICI Pru Liquid Fund - Regular - Growth      ICICI Prudential MF         Liquid      Regular          7.68          10.37               0.74
                Kotak Liquid Fund - Regular - Growth        Kotak Mahindra MF         Liquid      Regular          6.18           9.70               0.60
                 ABSL Liquid Fund - Regular - Growth Aditya Birla Sun Life MF         Liquid      Regular          5.14           8.76               0.79
        HDFC Short Term Debt Fund - Regular - Growth         HDFC Mutual Fund Short Duration      Regular          1.84           2.79               0.56
        SBI Magnum Gilt Fund - Regular Plan - Growth          SBI Mutual Fund           Gilt      Regular          1.52           2.11               0.77
Nippon India Gilt Securities Fund - Regular - Growth          Nippon India MF           Gilt      Regular          1.33           2.38               0.55
           HDFC Top 100 Fund - Regular Plan - Growth         HDFC Mutual Fund      Large Cap      Regular          1.06           1.70               1.55
       Mirae Asset Large Cap Fund - Regular - Growth           Mirae Asset MF      Large Cap      Regular          1.06           1.66               1.46
           ICICI Pru Bluechip Fund - Direct - Growth      ICICI Prudential MF      Large Cap       Direct          1.03           1.27               0.80
      Nippon India Large Cap Fund - Regular - Growth          Nippon India MF      Large Cap      Regular          1.00           1.68               1.51

---

## Q8: Top sectors in portfolio holdings by total market value

Rows returned: 10

        sector  holding_rows  total_market_value_cr  avg_weight_pct
       Banking            60               62840.29           10.87
            IT            40               38477.11           11.39
        Pharma            38               34606.10           10.72
    Automobile            33               34296.97            9.81
     Utilities            24               25108.63           11.06
Infrastructure            22               22433.39            8.73
          FMCG            21               21151.15           10.91
       Telecom            15               16051.45            9.71
        Energy            13               15286.54            9.07
   Diversified            14               13897.79           12.09

---

## Q9: Latest NAV coverage by fund house

Rows returned: 10

              fund_house  schemes_covered earliest_latest_date latest_latest_date
        HDFC Mutual Fund                5           2026-05-29         2026-05-29
     ICICI Prudential MF                5           2026-05-29         2026-05-29
         Nippon India MF                5           2026-05-29         2026-05-29
         SBI Mutual Fund                5           2026-05-29         2026-05-29
        Axis Mutual Fund                4           2026-05-29         2026-05-29
       Kotak Mahindra MF                4           2026-05-29         2026-05-29
Aditya Birla Sun Life MF                3           2026-05-29         2026-05-29
         DSP Mutual Fund                3           2026-05-29         2026-05-29
          Mirae Asset MF                3           2026-05-29         2026-05-29
         UTI Mutual Fund                3           2026-05-29         2026-05-29

---

## Q10: Benchmark averages by index

Rows returned: 7

     index_name  avg_close_value  min_close_value  max_close_value
   BSE_SMALLCAP         39375.03         23592.64         79075.39
    CRISIL_GILT          1779.53          1444.13          2302.79
  CRISIL_LIQUID          2639.93          2281.51          3046.00
       NIFTY100         17186.44         14128.86         21088.58
        NIFTY50         22089.36         17492.79         27798.72
       NIFTY500         23316.83         14426.04         38418.87
NIFTY_MIDCAP150         22076.53          8980.60         32990.66

---
