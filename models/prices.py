from models.utils import rows_to_df


def get_price_comparison(db) -> list:

    rows = db.execute(
        'SELECT name, category, price, store FROM expenses WHERE store != "" ORDER BY name'
    ).fetchall()
    df = rows_to_df(rows)
    if df.empty:
        return []

    result = []
    for name, grp in df.groupby('name'):
        min_price  = grp['price'].min()
        max_price  = grp['price'].max()
        result.append({
            'name':         name,
            'category':     grp['category'].iloc[0],
            'store_prices': grp.groupby('store')['price'].min().to_dict(),
            'min_price':    round(min_price, 2),
            'max_price':    round(max_price, 2),
            'best_store':   grp.loc[grp['price'].idxmin(), 'store'],
            'savings':      round(max_price - min_price, 2),
        })

    result.sort(key=lambda x: x['savings'], reverse=True)
    return result