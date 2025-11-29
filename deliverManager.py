import time
import random
import threading
from typing import List, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum


class EventArgs:
    """イベント引数の基底クラス"""
    pass


@dataclass
class RecipeEventArgs(EventArgs):
    """レシピイベント引数
    
    Attributes:
        recipe: 対象のレシピ
        success_count: 成功したレシピの総数
    """
    recipe: Optional['RecipeSO'] = None
    success_count: int = 0


class Event:
    """C#のeventに相当するクラス"""
    
    def __init__(self):
        self._handlers: List[Callable] = []
    
    def add_handler(self, handler: Callable):
        """イベントハンドラーを追加"""
        if handler not in self._handlers:
            self._handlers.append(handler)
    
    def remove_handler(self, handler: Callable):
        """イベントハンドラーを削除"""
        if handler in self._handlers:
            self._handlers.remove(handler)
    
    def invoke(self, sender, args: EventArgs = None):
        """イベントを発火"""
        for handler in self._handlers:
            handler(sender, args or EventArgs())


@dataclass
class KitchenObjectSO:
    """キッチンオブジェクトのデータクラス"""
    name: str
    object_id: int


@dataclass
class RecipeSO:
    """レシピのデータクラス"""
    name: str
    kitchen_object_so_list: List[KitchenObjectSO] = field(default_factory=list)


@dataclass
class RecipeListSO:
    """レシピリストのデータクラス"""
    recipe_so_list: List[RecipeSO] = field(default_factory=list)


class PlateKitchenObject:
    """皿のキッチンオブジェクト"""
    
    def __init__(self):
        self._kitchen_object_so_list: List[KitchenObjectSO] = []
    
    def add_kitchen_object(self, kitchen_object: KitchenObjectSO):
        """キッチンオブジェクトを追加"""
        self._kitchen_object_so_list.append(kitchen_object)
    
    def get_kitchen_object_so_list(self) -> List[KitchenObjectSO]:
        """キッチンオブジェクトリストを取得"""
        return self._kitchen_object_so_list.copy()


class KitchenGameManager:
    """キッチンゲームマネージャー（Singleton）
    
    ゲーム全体の状態を管理するシングルトンクラス。
    ゲームの開始・停止・状態確認を提供します。
    """
    
    _instance: Optional['KitchenGameManager'] = None
    _lock = threading.Lock()
    
    def __init__(self) -> None:
        self._is_game_playing = False
    
    @classmethod
    def get_instance(cls) -> 'KitchenGameManager':
        """スレッドセーフなSingletonインスタンスを取得
        
        Returns:
            KitchenGameManager: シングルトンインスタンス
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """インスタンスをリセット（テスト用）"""
        with cls._lock:
            cls._instance = None
    
    def is_game_playing(self) -> bool:
        """ゲームが進行中かどうか
        
        Returns:
            bool: ゲーム進行中の場合True
        """
        return self._is_game_playing
    
    def start_game(self) -> None:
        """ゲームを開始"""
        self._is_game_playing = True
    
    def stop_game(self) -> None:
        """ゲームを停止"""
        self._is_game_playing = False


class DeliveryManager:
    """配達管理クラス（Python版）
    
    レシピの生成、配達の検証、スコア管理を行うシングルトンクラス。
    定期的にレシピを生成し、プレイヤーが正しい料理を配達したかを判定します。
    
    Attributes:
        SPAWN_RECIPE_INTERVAL: レシピ生成の間隔（秒）
        MAX_WAITING_RECIPES: 同時に待機できる最大レシピ数
    """
    
    # クラス定数
    SPAWN_RECIPE_INTERVAL: float = 4.0
    MAX_WAITING_RECIPES: int = 4
    
    _instance: Optional['DeliveryManager'] = None
    _lock = threading.Lock()
    
    def __init__(self, recipe_list_so: RecipeListSO) -> None:
        """DeliveryManagerを初期化
        
        Args:
            recipe_list_so: 利用可能なレシピのリスト
        """
        # イベント定義
        self.on_recipe_spawned = Event()
        self.on_recipe_completed = Event()
        self.on_recipe_success = Event()
        self.on_recipe_failed = Event()
        
        # プライベート変数
        self._recipe_list_so = recipe_list_so
        self._waiting_recipe_so_list: List[RecipeSO] = []
        self._spawn_recipe_timer = 0.0
        self._successful_recipes_amount = 0
        self._last_update_time = time.time()
    
    @classmethod
    def get_instance(cls, recipe_list_so: Optional[RecipeListSO] = None) -> 'DeliveryManager':
        """スレッドセーフなSingletonインスタンスを取得
        
        Args:
            recipe_list_so: 初回作成時に必要なレシピリスト
        
        Returns:
            DeliveryManager: シングルトンインスタンス
        
        Raises:
            ValueError: 初回作成時にrecipe_list_soがNoneの場合
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    if recipe_list_so is None:
                        raise ValueError("初回作成時にはrecipe_list_soが必要です")
                    cls._instance = cls(recipe_list_so)
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """インスタンスをリセット（テスト用）"""
        with cls._lock:
            cls._instance = None
    
    def update(self) -> None:
        """フレーム更新処理（UnityのUpdate相当）
        
        一定時間ごとにレシピを生成します。
        ゲームループ内で定期的に呼び出す必要があります。
        """
        current_time = time.time()
        delta_time = current_time - self._last_update_time
        self._last_update_time = current_time
        
        self._spawn_recipe_timer -= delta_time
        
        if self._spawn_recipe_timer <= 0.0:
            self._spawn_recipe_timer = self.SPAWN_RECIPE_INTERVAL
            
            kitchen_game_manager = KitchenGameManager.get_instance()
            if (kitchen_game_manager.is_game_playing() and 
                len(self._waiting_recipe_so_list) < self.MAX_WAITING_RECIPES):
                
                # レシピリストが空でないことを確認
                if not self._recipe_list_so.recipe_so_list:
                    return
                
                # ランダムにレシピを選択
                waiting_recipe_so = random.choice(self._recipe_list_so.recipe_so_list)
                self._waiting_recipe_so_list.append(waiting_recipe_so)
                
                # イベント発火（レシピ情報を含む）
                args = RecipeEventArgs(
                    recipe=waiting_recipe_so,
                    success_count=self._successful_recipes_amount
                )
                self.on_recipe_spawned.invoke(self, args)
    
    def deliver_recipe(self, plate_kitchen_object: PlateKitchenObject) -> None:
        """レシピの材料と皿の材料が一致しているかどうかを確認する
        
        皿に盛られた食材が待機中のいずれかのレシピと完全一致するかチェックします。
        一致した場合は成功カウントを増やし、該当レシピを待機リストから削除します。
        
        Args:
            plate_kitchen_object: 検証対象の皿オブジェクト
        
        Note:
            - 材料の順序は考慮されません（セット比較）
            - O(n)の時間計算量で効率的に検証
        """
        plate_ingredients = plate_kitchen_object.get_kitchen_object_so_list()
        
        # 待機中のレシピを順にチェック
        for i, waiting_recipe_so in enumerate(self._waiting_recipe_so_list):
            # 材料数が一致するかチェック
            if len(waiting_recipe_so.kitchen_object_so_list) != len(plate_ingredients):
                continue
            
            # セットで比較（順序を無視して効率的に比較）
            recipe_set = set(waiting_recipe_so.kitchen_object_so_list)
            plate_set = set(plate_ingredients)
            
            # 材料が完全に一致した場合
            if recipe_set == plate_set:
                self._successful_recipes_amount += 1
                # リストから削除（popよりdelの方が意図が明確）
                del self._waiting_recipe_so_list[i]
                
                # 成功イベント発火（レシピ情報を含む）
                args = RecipeEventArgs(
                    recipe=waiting_recipe_so,
                    success_count=self._successful_recipes_amount
                )
                self.on_recipe_completed.invoke(self, args)
                self.on_recipe_success.invoke(self, args)
                return
        
        # 一致するレシピが見つからなかった場合
        args = RecipeEventArgs(success_count=self._successful_recipes_amount)
        self.on_recipe_failed.invoke(self, args)
    
    def get_waiting_recipe_so_list(self) -> List[RecipeSO]:
        """待機中のレシピリストを取得"""
        return self._waiting_recipe_so_list.copy()
    
    def get_successful_recipes_amount(self) -> int:
        """成功したレシピ数を取得"""
        return self._successful_recipes_amount


# 使用例
if __name__ == "__main__":
    # サンプルデータ作成
    tomato = KitchenObjectSO("Tomato", 1)
    lettuce = KitchenObjectSO("Lettuce", 2)
    bread = KitchenObjectSO("Bread", 3)
    
    # サンプルレシピ
    sandwich_recipe = RecipeSO("Sandwich", [bread, lettuce, tomato])
    salad_recipe = RecipeSO("Salad", [lettuce, tomato])
    
    recipe_list = RecipeListSO([sandwich_recipe, salad_recipe])
    
    # ゲームマネージャーとデリバリーマネージャーを初期化
    game_manager = KitchenGameManager.get_instance()
    game_manager.start_game()
    
    delivery_manager = DeliveryManager.get_instance(recipe_list)
    
    # イベントハンドラーの設定
    def on_recipe_spawned(sender, args):
        print("新しいレシピが生成されました！")
    
    def on_recipe_success(sender, args):
        print("レシピ配達成功！")
    
    def on_recipe_failed(sender, args):
        print("レシピ配達失敗...")
    
    delivery_manager.on_recipe_spawned.add_handler(on_recipe_spawned)
    delivery_manager.on_recipe_success.add_handler(on_recipe_success)
    delivery_manager.on_recipe_failed.add_handler(on_recipe_failed)
    
    # サンプル実行
    print("ゲーム開始...")
    
    # 5秒間更新処理を実行
    start_time = time.time()
    while time.time() - start_time < 5:
        delivery_manager.update()
        time.sleep(0.1)  # 100ms間隔で更新
    
    print(f"待機中のレシピ数: {len(delivery_manager.get_waiting_recipe_so_list())}")
    
    # サンプル配達テスト
    plate = PlateKitchenObject()
    plate.add_kitchen_object(bread)
    plate.add_kitchen_object(lettuce)
    plate.add_kitchen_object(tomato)
    
    print("サンドイッチを配達...")
    delivery_manager.deliver_recipe(plate)
    
    print(f"成功したレシピ数: {delivery_manager.get_successful_recipes_amount()}")