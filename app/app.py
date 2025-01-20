# discord.pyライブラリをインポート
import discord
from discord.ext import commands
from discord import app_commands
import random
from discord.ui import View, Button
import os
from dotenv import load_dotenv 
from keep_alive import keep_alive 

load_dotenv()
# Botのトークンを設定
TOKEN = os.getenv("TOKEN")  

# Discordのボットがアクセス可能な範囲を設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージ内容のアクセス許可
intents.guilds = True  # サーバー情報のアクセス許可
intents.guild_messages = True  # サーバー内メッセージのアクセス許可
intents.dm_messages = True  # DMメッセージのアクセス許可
intents.members = True  # メンバー情報のアクセス許可


# ボットのコマンドプレフィックス（コマンドの先頭に入力する文字）と意図を設定
bot = commands.Bot(command_prefix='/', intents=intents)

# ゲームに必要な変数を初期化
players = {}  # プレイヤーの辞書。キーはユーザーID、値はユーザー名 
roles = {}  # 各プレイヤーの役職
alive_players = {}  # 生存プレイヤー
dead_players = {}  # 死亡プレイヤー
game_started = False  # ゲームが開始したかどうか
day_time = False  # 現在が昼か夜か

night_time = False

votes = {}  # 投票結果の辞書
seer_target = None  # 占い師のターゲット
previous_night_victim = None  # 前夜に襲撃されたプレイヤー
seer_action_done = False  # 占い師が行動したか
wolf_action_done = False  # 人狼が行動したか
# 騎士の行動に必要な変数を追加
knight_protection_target = None  # 騎士が守るターゲット
knight_action_done = False  # 騎士が行動したか
# 必要なグローバル変数
cancel_votes = {}  # 中断に投票したプレイヤーのIDを保持する辞書


# 生存者の行動状況を追跡する辞書
player_actions_done = {}  # {player_id: True/False}




# 再投票回数を記録する変数
revote_count = 0  # グローバル変数として宣言



# 各役職の行動状態を追跡する辞書を追加
action_status = {
    "人狼": 0,
    "占い師": 0,
    "騎士": 0
}




# 各プレイヤーに役職を割り当てる関数
def assign_roles():
    global roles

    # プレイヤーIDリストとその順序のランダム化
    player_ids = list(players.keys())
    random.shuffle(player_ids)
    total_players = len(player_ids)

    # プレイヤー数に応じた役職の配布数を決定
    if total_players >= 10:
        fixed_roles = ["人狼", "人狼", "人狼", "占い師", "騎士", "村人", "村人"]
        random_role_pool = ["村人", "騎士"]
        random_role = random.choice(random_role_pool)
        role_distribution = fixed_roles + [random_role]
    elif total_players == 9:
        fixed_roles = ["人狼", "人狼", "人狼", "占い師", "騎士", "村人", "村人"]
        random_role_pool = ["村人", "騎士"]
        random_role = random.choice(random_role_pool)
        role_distribution = fixed_roles + [random_role]
    elif total_players == 8:
        fixed_roles = ["人狼", "人狼", "占い師", "騎士", "村人", "村人"]
        random_role_pool = ["村人", "騎士"]
        random_role = random.choice(random_role_pool)
        role_distribution = fixed_roles + [random_role]
    elif total_players == 7:
        fixed_roles = ["人狼", "人狼", "占い師", "騎士", "村人", "村人"]
        random_role_pool = ["占い師", "騎士", "狂人"]
        random_role = random.choice(random_role_pool)
        role_distribution = fixed_roles + [random_role]
    elif total_players == 6:
        fixed_roles = ["人狼", "占い師", "騎士", "村人", "狂人"]
        random_role_pool = ["村人"]
        random_role = random.choice(random_role_pool)
        role_distribution = fixed_roles + [random_role]
    elif total_players == 5:
        fixed_roles = ["人狼", "占い師", "騎士", "村人"]
        random_role_pool = ["村人", "狂人"]
        random_role = random.choice(random_role_pool)
        role_distribution = fixed_roles + [random_role]
    elif total_players == 4:
        fixed_roles = ["人狼", "占い師", "村人"]
        random_role_pool = ["村人", "騎士"]
        random_role = random.choice(random_role_pool)
        role_distribution = fixed_roles + [random_role]
    elif total_players == 3:
        role_distribution = ["人狼", "占い師", "村人"]
    else:
        raise ValueError("ゲームを開始するには少なくとも3人のプレイヤーが必要です。")

    # ランダムな役職割り当て
    random.shuffle(role_distribution)
    roles = dict(zip(player_ids, role_distribution))



# Botが起動したときの処理
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')  # Botのログイン確認
    await bot.tree.sync()  # スラッシュコマンドの同期





@bot.tree.command(name="menu", description="メインメニューを表示します")
async def menu(interaction: discord.Interaction):
    
    await interaction.response.send_message(
        "メインメニューを表示します。以下のボタンを使って操作してください。",
        view=MainMenu(),
        ephemeral=True
    )



#参加用view
class RecruitView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="ゲームに参加", style=discord.ButtonStyle.success)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global players
        if interaction.user.id not in players:
            players[interaction.user.id] = interaction.user.name
            await interaction.response.send_message(
                f"{interaction.user.name} がゲームに参加しました！ 現在の参加者: {', '.join(players.values())}", ephemeral=False
            )
        else:
            await interaction.response.send_message("既に参加しています！", ephemeral=True)




class MainMenu(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="募集", style=discord.ButtonStyle.primary)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.channel.send(
            "人狼ゲームの参加者を募集中です！ボタンを押してゲームに参加してください。", 
            view=RecruitView()
        )


    @discord.ui.button(label="ゲーム開始", style=discord.ButtonStyle.success)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        global game_started, roles, alive_players

        if game_started:
            await interaction.response.send_message("ゲームは既に開始されています。", ephemeral=True)
            return

        if 3 <= len(players) <= 10:
            game_started = True
            assign_roles()

            await interaction.response.send_message('ゲームが開始されました！各プレイヤーに役職をDMで送信します。')

            for player_id in players:
                user = await bot.fetch_user(player_id)
                try:
                    await user.send(f'あなたの役職は {roles[player_id]} です。')
                    alive_players[player_id] = players[player_id]
                except discord.Forbidden:
                    await interaction.response.send_message(
                        f'{players[player_id]} さんにDMを送信できませんでした。プライバシー設定を確認してください。',
                        ephemeral=True
                    )

            await start_day(interaction.channel)
        else:
            await interaction.response.send_message('ゲームを開始するには3人以上10人以下のプレイヤーが必要です。', ephemeral=True)

    @discord.ui.button(label="ヘルプ", style=discord.ButtonStyle.secondary)
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "このゲームは人狼ゲームです！\n以下のボタンを使って操作してください：\n"
            "- 「ゲームに参加」: ゲームに参加します。\n"
            "- 「ゲーム開始」: ゲームを開始します。\n"
            "- 「ヘルプ」: ゲームのルールや操作方法を表示します。\n\n"
            "不明点がある場合は管理者にお問い合わせください。",
            ephemeral=True
        )

    # 昼用ボタン
    @discord.ui.button(label="昼フェーズ", style=discord.ButtonStyle.primary)
    async def day_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        class DayActions(View):
            def __init__(self):
                super().__init__()

            @discord.ui.button(label="投票する", style=discord.ButtonStyle.success)
            async def vote_start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                # 投票ボタンを表示
                await interaction.response.send_message("投票を開始します。以下のボタンを使用してください。", view=VoteView(caller_id=interaction.user.id), ephemeral=True)


            @discord.ui.button(label="投票をパス", style=discord.ButtonStyle.secondary)
            async def pass_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                global game_started, day_time, votes, alive_players

                # 昼間でかつ生存しているプレイヤーのみがパス可能
                if game_started and day_time and interaction.user.id in alive_players:
                    if interaction.user.id not in votes:
                        votes[interaction.user.id] = 'パス'
                        await interaction.response.send_message(f'{players[interaction.user.id]} がパスに投票しました。', ephemeral=True)
                    else:
                        await interaction.response.send_message('既に投票しています。', ephemeral=True)

                    # 全員の投票が完了したら票を集計
                    if len(votes) == len(alive_players):
                        await tally_votes(interaction.channel)
                else:
                    await interaction.response.send_message('現在投票できる時間ではありません。', ephemeral=True)


        if game_started and day_time and interaction.user.id in alive_players:
            # 昼フェーズのボタンを表示
            await interaction.response.send_message(
                "昼フェーズのアクションを選択してください。",
                view=DayActions(),
                ephemeral=True
            )
        else:
            await interaction.response.send_message('現在行動できる時間ではありません。', ephemeral=True)




    # 夜用ボタン
    @discord.ui.button(label="夜フェーズ", style=discord.ButtonStyle.danger)
    async def night_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        class NightActions(View):
            def __init__(self):
                super().__init__()

            @discord.ui.button(label="占い (fortune)", style=discord.ButtonStyle.success)
            async def fortune_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                #ボタンを表示
                await interaction.response.send_message(
                    "占う対象を指定します。以下のボタンを使用してください。", 
                    view=FortuneView(caller_id=interaction.user.id), 
                    ephemeral=True
                )

            @discord.ui.button(label="守る (guard)", style=discord.ButtonStyle.primary)
            async def guard_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_message(
                    "守りを実行します。守るプレイヤーを選択してください。", 
                    view=guardView(caller_id=interaction.user.id), 
                    ephemeral=True
                )

            @discord.ui.button(label="襲撃 (attack)", style=discord.ButtonStyle.danger)
            async def attack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_message(
                    "襲撃を実行します。襲撃するプレイヤーを選択してください。", 
                    view=attackView(caller_id=interaction.user.id), 
                    ephemeral=True
                )

            
            @discord.ui.button(label="何もせず寝る(村人／狂人)", style=discord.ButtonStyle.secondary)
            async def night_pass_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                global game_started, day_time, votes, alive_players

                # 生存しているプレイヤーのみがパス可能
                if game_started and night_time and interaction.user.id in alive_players:

                     # 行動完了を記録
                    await interaction.response.send_message('行動をスキップします', ephemeral=True)
                    await record_action(interaction.user.id, interaction.channel)

                else:
                    await interaction.response.send_message('現在選択できません', ephemeral=True)




        if game_started and night_time and interaction.user.id in alive_players:
            # 夜フェーズのボタンを表示
            await interaction.response.send_message(
                "夜フェーズのアクションを選択してください。\n"
                "村人や狂人、または行動をスキップしたい人は”何もせず寝る”を選択してください。",
                view=NightActions(),
                ephemeral=True
            )
        else:
            await interaction.response.send_message('現在行動できる時間ではありません。', ephemeral=True)


    @discord.ui.button(label="ヘルプ", style=discord.ButtonStyle.secondary)
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "このゲームは人狼ゲームです！\n以下のボタンを使って操作してください：\n"
            "- 「昼フェーズ」: 昼間のアクションを選択します。\n"
            "- 「夜フェーズ」: 夜間のアクションを選択します。\n"
            "- 「ヘルプ」: ゲームのルールや操作方法を表示します。\n\n"
            "不明点がある場合は管理者にお問い合わせください。",
            ephemeral=True
        )

    



# 投票ボタンのクラスを修正
class VoteView(View):
    def __init__(self, caller_id):
        super().__init__()
        # 現在生存しているプレイヤーのボタンを動的に追加
        for player_id, player_name in alive_players.items():
            if player_id != caller_id:
                self.add_item(VoteButton(player_id, player_name))

class VoteButton(Button):
    def __init__(self, player_id, player_name):
        # ボタンのラベルをプレイヤー名に設定
        super().__init__(label=player_name, style=discord.ButtonStyle.primary)
        self.player_id = player_id  # ボタンに紐づくプレイヤーID

    async def callback(self, interaction: discord.Interaction):
        global votes, alive_players

        # 投票者が既に投票していない場合のみ受け付ける
        if interaction.user.id not in votes:
            votes[interaction.user.id] = self.player_id  # 投票結果を記録
            await interaction.response.send_message(
                f"{players[interaction.user.id]} が {players[self.player_id]} に投票しました。",
                ephemeral=True
            )

            # 全員の投票が完了したら集計
            if len(votes) == len(alive_players):
                await tally_votes(interaction.channel)
        else:
            await interaction.response.send_message("既に投票しています。", ephemeral=True)


class guardView(View):
    def __init__(self, caller_id):
        super().__init__()
        # 呼び出したプレイヤー（caller_id）を除いてボタンを生成
        for player_id, player_name in alive_players.items():
            if player_id != caller_id:
                self.add_item(guardButton(player_id, player_name))


class guardButton(Button):
    def __init__(self, player_id, player_name):
        super().__init__(label=player_name, style=discord.ButtonStyle.primary)
        self.player_id = player_id

    async def callback(self, interaction: discord.Interaction):
        global knight_protection_target, action_status

        if game_started and night_time and interaction.user.id in alive_players and roles[interaction.user.id] == '騎士':
            knight_protection_target = self.player_id
            #action_status["騎士"] += 1
            await interaction.response.send_message(
                f'{players[knight_protection_target]} が今夜守られます。', 
                ephemeral=True
            )
            # 行動完了を記録
            await record_action(interaction.user.id, interaction.channel)
        else:
            await interaction.response.send_message('このアクションを実行する権限がありません。', ephemeral=True)


class FortuneView(View):
    def __init__(self, caller_id):
        super().__init__()
        # 呼び出したプレイヤー（caller_id）を除いてボタンを生成
        for player_id, player_name in alive_players.items():
            if player_id != caller_id:
                self.add_item(FortuneButton(player_id, player_name))

class FortuneButton(Button):
    def __init__(self, player_id, player_name):
        super().__init__(label=player_name, style=discord.ButtonStyle.primary)
        self.player_id = player_id

    async def callback(self, interaction: discord.Interaction):
        global seer_target, alive_players

        # 占い師の行動を記録
        if game_started and night_time and interaction.user.id in alive_players and roles[interaction.user.id] == '占い師':
            seer_target = self.player_id
            if roles[seer_target] == '人狼':
                result = '黒'
            else:
                result = '白'
            await interaction.response.send_message(
                f'{players[seer_target]} の占い結果は {result} です。',
                ephemeral=True
            )
            # 行動完了を記録
            await record_action(interaction.user.id, interaction.channel)
        else:
            await interaction.response.send_message('占いを実行できません。', ephemeral=True)




class attackView(View):
    def __init__(self, caller_id):
        super().__init__()
        # 呼び出したプレイヤー（caller_id）を除いてボタンを生成
        for player_id, player_name in alive_players.items():
            if player_id != caller_id:
                self.add_item(attackButton(player_id, player_name))



class attackButton(Button):
    def __init__(self, player_id, player_name):
        super().__init__(label=player_name, style=discord.ButtonStyle.primary)
        self.player_id = player_id

    async def callback(self, interaction: discord.Interaction):
        global game_started, night_time, alive_players, previous_night_victim, wolf_action_done, knight_protection_target, action_status

        if game_started and night_time and interaction.user.id in alive_players and roles[interaction.user.id] == '人狼':
            target_id = self.player_id



            previous_night_victim = target_id  # 襲撃対象を記録
            await interaction.response.send_message(f'{players[target_id]} を今夜襲撃します。', ephemeral=True)


            # 行動完了を記録
            await record_action(interaction.user.id, interaction.channel)
        else:
            await interaction.response.send_message('このアクションを実行する権限がありません。', ephemeral=True)







# 勝敗判定関数
async def check_victory(channel):
    alive_werewolves = sum(1 for player_id, role in roles.items() if role == '人狼' and player_id in alive_players)
    alive_non_werewolves = sum(1 for player_id in alive_players if roles[player_id] != '人狼')
    
    if alive_werewolves == 0:
        # 人狼が全滅している場合
        await channel.send("村人陣営の勝利！")
        reset_game()
        return True  # ゲーム終了
    
    if alive_werewolves >= alive_non_werewolves:
        # 人狼の数が非人狼と同じか多い場合
        await channel.send("人狼(狂人)陣営の勝利！")
        reset_game()
        return True  # ゲーム終了
    
    return False  # ゲーム続行

# 投票の集計
async def tally_votes(channel):
    global day_time, alive_players, dead_players, revote_count

    vote_counts = {}
    for vote in votes.values():
        if vote in vote_counts:
            vote_counts[vote] += 1
        else:
            vote_counts[vote] = 1

    if 'パス' in vote_counts and vote_counts['パス'] > len(alive_players) / 2:
        await channel.send('処刑がパスされました。')
        revote_count = 0  # 再投票回数をリセット
        await start_night(channel)
    else:
        most_votes = max(vote_counts.values())
        top_candidates = [candidate for candidate, count in vote_counts.items() if count == most_votes]

        # 同票数であれば再投票
        if len(top_candidates) > 1:
            revote_count += 1  # 再投票回数を増加
            if revote_count >= 2:
                # 二回連続で再投票となった場合、ランダムに一人を処刑
                to_be_executed = random.choice(list(alive_players.keys()))
                dead_players[to_be_executed] = alive_players[to_be_executed]
                del alive_players[to_be_executed]
                await channel.send(f'再投票が続いたため、ランダムで {players[to_be_executed]} が処刑されました。')
                
                revote_count = 0  # 再投票回数をリセット
                # 勝敗判定を昼フェーズ開始時に行う
                game_ended = await check_victory(channel)
                if game_ended:
                    return  # 勝敗が確定した場合、ゲームを終了する
                else:
                    await start_night(channel)
            else:
                await channel.send("投票が同数となりました。もう一度投票してください。\n"
                                   "連続で再投票となった場合、ランダムで一人処刑されます。")
                await start_day(channel)
        else:
            to_be_executed = top_candidates[0]
            if to_be_executed in alive_players:
                dead_players[to_be_executed] = alive_players[to_be_executed]
                del alive_players[to_be_executed]
                await channel.send(f'{players[to_be_executed]} が処刑されました。')

                revote_count = 0  # 再投票回数をリセット
                # 勝敗判定を昼フェーズ開始時に行う
                game_ended = await check_victory(channel)
                if game_ended:
                    return  # 勝敗が確定した場合、ゲームを終了する
                else:
                    await start_night(channel)




# 昼間フェーズを開始する
async def start_day(channel):
    global night_time, day_time, votes, previous_night_victim, alive_players, dead_players, action_status, target_id, knight_protection_target

    # 前夜に襲撃されたプレイヤーを死亡状態にする
    if previous_night_victim is not None and previous_night_victim != knight_protection_target:
        if previous_night_victim in alive_players:
            dead_players[previous_night_victim] = alive_players[previous_night_victim]
            del alive_players[previous_night_victim]
            await channel.send(f'{players[previous_night_victim]} が昨夜襲撃され、死亡しました。')
        previous_night_victim = None  # 襲撃者をリセット

    # 勝敗判定を昼フェーズ開始時に行う
    game_ended = await check_victory(channel)
    if game_ended:
        return  # 勝敗が確定した場合、ゲームを終了する

    # 勝敗が確定していない場合、昼フェーズを開始する
    day_time = True
    night_time = False
    votes = {}
    action_status = {role: 0 for role in action_status}  # 各役職の行動完了数をリセット
    knight_protection_target = None
    await channel.send(
        '🌄日が昇りました。全員で話し合い、投票してください。', 
        view=MainMenu()
        )



# 夜間フェーズを開始する
async def start_night(channel):
    global night_time, day_time, player_actions_done

    day_time = False
    night_time = True
    player_actions_done = {player_id: False for player_id in alive_players}  # 生存者の行動状況をリセット
    await channel.send(
        '🌙夜が訪れました。各役職は行動してください。', 
        view=MainMenu()
        )


"""

# 夜フェーズを開始する
async def start_night(channel):
    global day_time, night_time, votes, action_status

    day_time = False
    night_time = True
    votes = {}
    action_status = {role: 0 for role in action_status}  # 各役職の行動完了数をリセット

    await channel.send("夜が訪れました。各プレイヤーは行動を開始してください。")

    # 夜フェーズが開始した際にメインメニューを表示
    await menu(channel)

"""

"""

# 夜の行動が完了したかを確認する関数
async def check_night_actions_done(channel):
    global roles, alive_players, action_status

    alive_roles_count = {role: sum(1 for player_id in alive_players if roles[player_id] == role)
                         for role in action_status.keys()}

    # 全ての役職のプレイヤーが行動を完了したかを確認
    if all(action_status[role] >= alive_roles_count[role] for role in alive_roles_count):
        await start_day(channel)
"""

# 夜の行動が完了したかを確認する関数
async def check_all_actions_done(channel):
    global player_actions_done, alive_players

    # すべての生存プレイヤーが行動を終えた場合
    if all(player_actions_done.get(player_id, False) for player_id in alive_players):
        await channel.send("🌅 夜が明けました。昼フェーズに移行します。")
        await start_day(channel)



# 夜の各アクションで行動完了を記録
async def record_action(player_id, channel):
    global player_actions_done

    # プレイヤーの行動を完了としてマーク
    player_actions_done[player_id] = True

    # すべてのプレイヤーが行動済みか確認
    await check_all_actions_done(channel)





# 中断コマンドを実装
@bot.tree.command(name="cancel", description="ゲームを途中で中断します（参加者の過半数が必要）")
async def cancel(interaction: discord.Interaction):
    global cancel_votes, game_started

    # ゲームが開始している場合のみ中断を受付
    if game_started:
        # すでに中断投票していない場合のみ、投票をカウント
        if interaction.user.id not in cancel_votes:
            cancel_votes[interaction.user.id] = players[interaction.user.id]
            await interaction.response.send_message(f'{players[interaction.user.id]} がゲームの中断に投票しました。')

            # 現在の中断投票数が過半数に達しているか確認
            if len(cancel_votes) > len(alive_players) / 2:
                await interaction.channel.send('参加者の過半数がゲームの中断に賛成しました。ゲームを終了します。')
                reset_game()  # ゲームをリセットして終了
            else:
                remaining_votes = (len(alive_players) // 2 + 1) - len(cancel_votes)
                await interaction.channel.send(f'中断するにはあと{remaining_votes}人の賛成が必要です。')
        else:
            await interaction.response.send_message('すでに中断に投票済みです。', ephemeral=True)
    else:
        await interaction.response.send_message('ゲームは開始されていません。', ephemeral=True)

# ゲームをリセットする関数
def reset_game():
    global players, roles, alive_players, dead_players, game_started, day_time, night_time, votes, seer_target, previous_night_victim, seer_action_done, wolf_action_done, cancel_votes

    players = {}
    roles = {}
    alive_players = {}
    dead_players = {}
    game_started = False
    day_time = False
    night_time = False
    votes = {}
    seer_target = None
    previous_night_victim = None
    seer_action_done = False
    wolf_action_done = False
    cancel_votes = {}  # 中断票もリセット

keep_alive()

# Botの実行開始
bot.run(TOKEN)
